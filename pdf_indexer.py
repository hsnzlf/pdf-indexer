#!/usr/bin/env python3
"""
pdf_toc_builder_gui.py
اپلیکیشن گرافیکی ساده برای ساخت/اصلاح ایندکس (Outline/Bookmark) فصل‌ها
در هر فایل PDF حجیم، بر اساس فهرست مطالب چاپی خود کتاب.

نصب پیش‌نیاز:
    pip install pymupdf

اجرا:
    python3 pdf_toc_builder_gui.py

---------------------------------------------------------------
گردش کار در برنامه:
  1) فایل PDF را باز کنید.
  2) با دکمه‌های Prev/Next صفحات مقدماتی کتاب را ورق بزنید تا صفحاتی
     که فهرست مطالب (Table of Contents) واقعی در آنهاست را پیدا کنید.
  3) شماره صفحه شروع و پایان فهرست را وارد کنید و «پارس فهرست» را بزنید.
  4) نتیجه در جدول نمایش داده می‌شود؛ می‌توانید هر سلول را با دوبار
     کلیک ویرایش کنید (برای اصلاح مواردی که فرمت عجیب داشته‌اند).
  5) اگر فایل فقط بخشی از فصل‌های موجود در فهرست را دارد (جلد دوم/سوم
     یک ست چندجلدی)، اولین و آخرین ردیف متعلق به همین فایل را با
     دکمه‌های «شروع از این ردیف» و «پایان در این ردیف» مشخص کنید.
  6) ردیف anchor (پیش‌فرض: همان ردیف شروع) را انتخاب کنید و «تشخیص
     خودکار صفحه واقعی» را بزنید تا افست صفحه چاپی نسبت به PDF محاسبه شود.
  7) «ساخت PDF ایندکس‌شده» را بزنید و مسیر ذخیره را انتخاب کنید.
"""

import os
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

try:
    import fitz  # PyMuPDF
except ImportError:
    raise SystemExit("ابتدا نصب کنید: pip install pymupdf")


class TocBuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Chapter Index Builder")
        self.root.geometry("720x260")

        self.doc = None
        self.pdf_path = None
        self.current_preview_page = 0

        self.entries = []  # list of dicts: {level, title, printed_page}
        self.trim_start_idx = None
        self.trim_end_idx = None
        self.anchor_idx = None
        self.offset = None

        self._build_ui()

    # ---------------------------------------------------------- UI BUILD
    def _build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")

        auto_frame = ttk.LabelFrame(self.root, text="ساخت ایندکس PDF", padding=14)
        auto_frame.pack(fill="x", padx=10, pady=10)
        big_btn = tk.Button(auto_frame, text="📄  انتخاب فایل PDF و ساخت خودکار",
                             command=self.run_full_auto, font=("Segoe UI", 13, "bold"),
                             bg="#2d6cdf", fg="white", padx=16, pady=12)
        big_btn.pack(pady=4)
        self.lbl_auto_status = ttk.Label(auto_frame, text="", font=("Segoe UI", 10))
        self.lbl_auto_status.pack(pady=(6, 0))

        toggle_frame = ttk.Frame(self.root, padding=(10, 0))
        toggle_frame.pack(fill="x")
        self.advanced_visible = False
        self.btn_toggle_advanced = ttk.Button(toggle_frame, text="▾ نمایش تنظیمات پیشرفته / دستی",
                                               command=self.toggle_advanced)
        self.btn_toggle_advanced.pack(anchor="w")

        self.advanced_frame = ttk.Frame(self.root)
        # عمداً pack نمی‌شود؛ فقط با toggle_advanced نمایش داده می‌شود

        top = self.advanced_frame

        ttk.Button(top, text="باز کردن PDF (حالت دستی)...", command=self.open_pdf).pack(side="left")
        self.lbl_file = ttk.Label(top, text="فایلی انتخاب نشده")
        self.lbl_file.pack(side="left", padx=10)

        # ---- Preview area ----
        prev_frame = ttk.LabelFrame(top, text="پیش‌نمایش صفحات (برای پیدا کردن محدوده فهرست مطالب)", padding=8)
        prev_frame.pack(fill="both", expand=False, padx=8, pady=4)

        nav = ttk.Frame(prev_frame)
        nav.pack(fill="x")
        ttk.Button(nav, text="< صفحه قبل", command=self.prev_page).pack(side="left")
        ttk.Button(nav, text="صفحه بعد >", command=self.next_page).pack(side="left", padx=4)
        ttk.Label(nav, text="  برو به صفحه:").pack(side="left", padx=(20, 2))
        self.entry_goto = ttk.Entry(nav, width=6)
        self.entry_goto.pack(side="left")
        ttk.Button(nav, text="برو", command=self.goto_page).pack(side="left", padx=4)
        self.lbl_pagenum = ttk.Label(nav, text="صفحه: -")
        self.lbl_pagenum.pack(side="left", padx=20)

        self.txt_preview = tk.Text(prev_frame, height=10, wrap="word")
        self.txt_preview.pack(fill="both", expand=True, pady=4)

        # ---- Parse controls ----
        parse_frame = ttk.LabelFrame(top, text="پارس فهرست مطالب", padding=8)
        parse_frame.pack(fill="x", padx=8, pady=4)

        ttk.Label(parse_frame, text="صفحه شروع فهرست:").grid(row=0, column=0, sticky="w")
        self.entry_start = ttk.Entry(parse_frame, width=8)
        self.entry_start.grid(row=0, column=1, padx=4)

        ttk.Label(parse_frame, text="صفحه پایان فهرست:").grid(row=0, column=2, sticky="w")
        self.entry_end = ttk.Entry(parse_frame, width=8)
        self.entry_end.grid(row=0, column=3, padx=4)

        ttk.Label(parse_frame, text="کلیدواژه سطح ۱ (مثل PART):").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.entry_part_kw = ttk.Entry(parse_frame, width=12)
        self.entry_part_kw.insert(0, "PART")
        self.entry_part_kw.grid(row=1, column=1, padx=4, pady=(6, 0))

        ttk.Label(parse_frame, text="برچسب سطح ۲ (مثل Chapter):").grid(row=1, column=2, sticky="w", pady=(6, 0))
        self.entry_chapter_label = ttk.Entry(parse_frame, width=12)
        self.entry_chapter_label.insert(0, "Chapter")
        self.entry_chapter_label.grid(row=1, column=3, padx=4, pady=(6, 0))

        ttk.Button(parse_frame, text="پارس فهرست", command=self.parse_contents).grid(row=0, column=4, rowspan=2, padx=20)

        # ---- Table ----
        table_frame = ttk.LabelFrame(top, text="فهرست استخراج‌شده (دوبار کلیک برای ویرایش)", padding=8)
        table_frame.pack(fill="both", expand=True, padx=8, pady=4)

        cols = ("level", "title", "page")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("level", text="سطح")
        self.tree.heading("title", text="عنوان")
        self.tree.heading("page", text="صفحه چاپی")
        self.tree.column("level", width=50, anchor="center")
        self.tree.column("title", width=650)
        self.tree.column("page", width=90, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", self.edit_cell)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # ---- Row action buttons ----
        row_actions = ttk.Frame(top, padding=(8, 0))
        row_actions.pack(fill="x")
        ttk.Button(row_actions, text="افزودن ردیف", command=self.add_row).pack(side="left")
        ttk.Button(row_actions, text="حذف ردیف", command=self.delete_row).pack(side="left", padx=4)
        ttk.Button(row_actions, text="شروع از این ردیف", command=self.set_trim_start).pack(side="left", padx=(20, 4))
        ttk.Button(row_actions, text="پایان در این ردیف", command=self.set_trim_end).pack(side="left", padx=4)
        self.lbl_trim = ttk.Label(row_actions, text="محدوده: کل جدول")
        self.lbl_trim.pack(side="left", padx=20)

        # ---- Anchor / offset ----
        anchor_frame = ttk.LabelFrame(top, text="تعیین افست صفحه (Anchor)", padding=8)
        anchor_frame.pack(fill="x", padx=8, pady=4)

        ttk.Button(anchor_frame, text="این ردیف را Anchor کن", command=self.set_anchor).pack(side="left")
        self.lbl_anchor = ttk.Label(anchor_frame, text="Anchor: تعیین نشده")
        self.lbl_anchor.pack(side="left", padx=10)

        ttk.Label(anchor_frame, text="جستجو از صفحه:").pack(side="left", padx=(20, 2))
        self.entry_search_start = ttk.Entry(anchor_frame, width=8)
        self.entry_search_start.pack(side="left")

        ttk.Button(anchor_frame, text="تشخیص خودکار صفحه واقعی", command=self.auto_detect_offset).pack(side="left", padx=10)
        self.lbl_offset = ttk.Label(anchor_frame, text="افست: -")
        self.lbl_offset.pack(side="left", padx=10)

        ttk.Label(anchor_frame, text="  یا افست دستی:").pack(side="left", padx=(20, 2))
        self.entry_manual_offset = ttk.Entry(anchor_frame, width=8)
        self.entry_manual_offset.pack(side="left")
        ttk.Button(anchor_frame, text="اعمال افست دستی", command=self.apply_manual_offset).pack(side="left", padx=4)

        # ---- Build output ----
        out_frame = ttk.Frame(top, padding=8)
        out_frame.pack(fill="x")
        ttk.Button(out_frame, text="ساخت PDF ایندکس‌شده...", command=self.build_output).pack(side="left")
        self.lbl_status = ttk.Label(out_frame, text="")
        self.lbl_status.pack(side="left", padx=10)

    def toggle_advanced(self):
        if self.advanced_visible:
            self.advanced_frame.pack_forget()
            self.btn_toggle_advanced.config(text="▾ نمایش تنظیمات پیشرفته / دستی")
        else:
            self.advanced_frame.pack(fill="both", expand=True, padx=8, pady=4)
            self.btn_toggle_advanced.config(text="▴ پنهان کردن تنظیمات پیشرفته / دستی")
        self.advanced_visible = not self.advanced_visible

    # ---------------------------------------------------------- FULL AUTO PIPELINE
    def run_full_auto(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        self.lbl_auto_status.config(text="در حال پردازش...")
        self.root.update_idletasks()
        threading.Thread(target=self._auto_worker, args=(path,), daemon=True).start()

    def _auto_worker(self, path):
        try:
            doc = fitz.open(path)
        except Exception as e:
            self._auto_fail(f"باز کردن فایل ناموفق بود:\n{e}")
            return

        total_pages = len(doc)

        # 1) پیدا کردن محدوده فهرست مطالب (به‌دنبال خط مستقل CONTENTS، نه VIDEO CONTENTS)
        contents_start = None
        scan_limit = min(80, total_pages)
        for pno in range(scan_limit):
            page_text = doc[pno].get_text("text")
            for ln in page_text.split("\n"):
                if ln.strip().upper() == "CONTENTS":
                    contents_start = pno
                    break
            if contents_start is not None:
                break

        if contents_start is None:
            self._auto_fail("صفحه‌ای با تیتر «CONTENTS» در ۸۰ صفحه اول پیدا نشد.\n"
                             "لطفاً از حالت دستی (پایین پنجره) استفاده کنید و بازه فهرست را خودتان مشخص کنید.")
            return

        contents_end = None
        for pno in range(contents_start + 1, min(contents_start + 20, total_pages)):
            page_text = doc[pno].get_text("text")
            if "VIDEO CONTENTS" in page_text.upper():
                contents_end = pno
                break
        if contents_end is None:
            contents_end = min(contents_start + 8, total_pages)

        # 2) پارس فهرست با کلیدواژه‌های پیش‌فرض PART/Chapter
        combined = ""
        for pno in range(contents_start, contents_end):
            combined += doc[pno].get_text("text")
        entries = self._parse_lines(combined, "PART", "Chapter")

        if not entries:
            self._auto_fail("هیچ فصلی از فهرست مطالب پارس نشد.\nاز حالت دستی استفاده کنید.")
            return

        # 3) پیدا کردن اولین فصلی که واقعاً در همین فایل موجود است (anchor خودکار)
        def title_search_text(title):
            return re.sub(r'^\S+\s+\d+:\s*', '', title).strip()[:60]

        level2_entries = [(idx, title, pp) for idx, (level, title, pp) in enumerate(entries)
                           if level == 2 and pp is not None]

        anchor_idx = None
        found_page = None
        offset = None
        search_from = contents_end + 1

        for pos, (idx, title, printed_page) in enumerate(level2_entries):
            search_text = title_search_text(title)
            if len(search_text) < 8:
                continue
            self.root.after(0, lambda t=title: self.lbl_auto_status.config(text=f"در حال بررسی: {t[:45]}..."))

            candidate_found = None
            for pno in range(search_from, total_pages):
                if doc[pno].search_for(search_text):
                    candidate_found = pno
                    break
            if candidate_found is None:
                continue

            candidate_offset = candidate_found - printed_page

            # تأیید: فصل‌های بعدی هم باید تقریباً همان‌جایی که این افست پیش‌بینی می‌کند پیدا شوند.
            # اگر تأیید نشد، این تطابق تصادفی بوده (مثلاً یک زیرعنوان مشابه در فصل دیگری)؛ ادامه می‌دهیم.
            verified_checks = 0
            verified_ok = True
            for (idx2, title2, printed_page2) in level2_entries[pos + 1: pos + 4]:
                expected = printed_page2 + candidate_offset
                if expected < 0 or expected >= total_pages:
                    verified_ok = False
                    break
                search_text2 = title_search_text(title2)
                if len(search_text2) < 8:
                    continue
                lo, hi = max(0, expected - 3), min(total_pages, expected + 4)
                hit = any(doc[p2].search_for(search_text2) for p2 in range(lo, hi))
                if not hit:
                    verified_ok = False
                    break
                verified_checks += 1
                if verified_checks >= 2:
                    break

            if verified_ok and verified_checks >= 1:
                anchor_idx = idx
                found_page = candidate_found
                offset = candidate_offset
                break
            # وگرنه ادامه بده و کاندید بعدی را امتحان کن

        if anchor_idx is None:
            self._auto_fail("هیچ‌کدام از عنوان‌های فصل‌ها در بدنه PDF پیدا نشد.\n"
                             "ممکن است فرمت فهرست این کتاب متفاوت باشد؛ از حالت دستی استفاده کنید.")
            return

        # (افست همان candidate_offset تأییدشده از حلقه بالاست)

        # اگر ردیف قبل از anchor از نوع PART بود، آن را هم نگه دار
        start_idx = anchor_idx
        if anchor_idx > 0 and entries[anchor_idx - 1][0] == 1:
            start_idx = anchor_idx - 1

        subset = entries[start_idx:]

        # ارث‌بری صفحه برای ردیف‌های PART بدون شماره صفحه
        for idx in range(len(subset)):
            if subset[idx][2] is None:
                for j in range(idx + 1, len(subset)):
                    if subset[j][2] is not None:
                        subset[idx] = [subset[idx][0], subset[idx][1], subset[j][2]]
                        break

        toc = []
        for level, title, printed_page in subset:
            if printed_page is None:
                continue
            pdf_page = printed_page + offset
            if pdf_page < 0 or pdf_page >= total_pages:
                continue
            toc.append([level, title, pdf_page + 1])

        if not toc:
            self._auto_fail("پس از محاسبه افست، هیچ ورودی معتبری باقی نماند.\nاز حالت دستی استفاده کنید.")
            return
        if toc[0][0] != 1:
            toc[0][0] = 1

        out_path = os.path.join(os.path.dirname(path),
                                 os.path.splitext(os.path.basename(path))[0] + "_indexed.pdf")
        try:
            doc.set_toc(toc)
            doc.save(out_path)
        except Exception as e:
            self._auto_fail(f"ساخت فایل نهایی با خطا مواجه شد:\n{e}")
            return

        # نمایش نتیجه در جدول دستی هم (برای بازبینی اختیاری)
        def on_done():
            self.doc = fitz.open(path)
            self.pdf_path = path
            self.lbl_file.config(text=f"{os.path.basename(path)}  ({len(self.doc)} صفحه)")
            self.entries = subset
            self.offset = offset
            self.trim_start_idx = 0
            self.trim_end_idx = len(subset) - 1
            self._update_trim_label()
            self.refresh_table()
            self.lbl_offset.config(text=f"افست: {offset}")
            self.lbl_auto_status.config(text=f"✅ انجام شد ({len(toc)} فصل) → {out_path}")
            messagebox.showinfo("انجام شد", f"فایل ایندکس‌شده ساخته شد:\n{out_path}\n\n{len(toc)} ورودی ایندکس اضافه شد.")

        self.root.after(0, on_done)

    def _auto_fail(self, msg):
        def show():
            self.lbl_auto_status.config(text="❌ ناموفق")
            messagebox.showerror("حالت خودکار ناموفق بود", msg)
        self.root.after(0, show)

    # ---------------------------------------------------------- PDF / PREVIEW
    def open_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        try:
            self.doc = fitz.open(path)
        except Exception as e:
            messagebox.showerror("خطا", f"باز کردن فایل ناموفق بود:\n{e}")
            return
        self.pdf_path = path
        self.lbl_file.config(text=f"{os.path.basename(path)}  ({len(self.doc)} صفحه)")
        self.current_preview_page = 0
        self.show_preview_page()

    def show_preview_page(self):
        if not self.doc:
            return
        self.txt_preview.delete("1.0", "end")
        p = self.current_preview_page
        if 0 <= p < len(self.doc):
            self.txt_preview.insert("1.0", self.doc[p].get_text("text"))
        self.lbl_pagenum.config(text=f"صفحه: {p}  (از {len(self.doc)-1})")

    def prev_page(self):
        if self.doc and self.current_preview_page > 0:
            self.current_preview_page -= 1
            self.show_preview_page()

    def next_page(self):
        if self.doc and self.current_preview_page < len(self.doc) - 1:
            self.current_preview_page += 1
            self.show_preview_page()

    def goto_page(self):
        if not self.doc:
            return
        try:
            p = int(self.entry_goto.get())
        except ValueError:
            return
        if 0 <= p < len(self.doc):
            self.current_preview_page = p
            self.show_preview_page()

    # ---------------------------------------------------------- PARSE
    def _parse_lines(self, combined, part_kw, chapter_label):
        lines = [l.rstrip("\r\n") for l in combined.split("\n")]
        entries = []
        i = 0
        part_re = re.compile(rf'^{re.escape(part_kw)}\s+([IVXLCDM]+|\d+)\b\s*(.*)$', re.IGNORECASE)
        pure_num_re = re.compile(r'^\d{1,4}$')
        combo_re = re.compile(r'^(\d{1,4})\s+(\S.*)$')
        part_or_marker_re = re.compile(rf'^\d{{1,4}}$|^{re.escape(part_kw)}\s+[IVXLCDM\d]', re.IGNORECASE)

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            m = part_re.match(line)
            if m:
                num, rest = m.groups()
                rest = re.sub(r'\t?\s*\d+\s*$', '', rest).strip()
                entries.append([1, f"{part_kw} {num} {rest}".strip(), None])
                i += 1
                continue

            if pure_num_re.match(line):
                chnum = line
                i += 1
                title_lines = []
                page_num = None
                while i < len(lines):
                    l2 = lines[i].strip()
                    i += 1
                    if not l2:
                        continue
                    mm = re.search(r',\s*(\d{1,5})\s*$', l2)
                    if mm:
                        title_lines.append(l2[:mm.start()].strip())
                        page_num = int(mm.group(1))
                        break
                    else:
                        title_lines.append(l2)
                title = " ".join(title_lines).strip()
                entries.append([2, f"{chapter_label} {chnum}: {title}", page_num])
                while i < len(lines):
                    l3 = lines[i].strip()
                    if not l3:
                        i += 1
                        continue
                    if part_or_marker_re.match(l3) or combo_re.match(l3):
                        break
                    i += 1
                continue

            m2 = combo_re.match(line)
            if m2:
                chnum, rest = m2.groups()
                i += 1
                mm = re.search(r',\s*(\d{1,5})\s*$', rest)
                title_lines = []
                page_num = None
                if mm:
                    title_lines = [rest[:mm.start()].strip()]
                    page_num = int(mm.group(1))
                else:
                    title_lines = [rest]
                    while i < len(lines):
                        l2 = lines[i].strip()
                        i += 1
                        if not l2:
                            continue
                        mm = re.search(r',\s*(\d{1,5})\s*$', l2)
                        if mm:
                            title_lines.append(l2[:mm.start()].strip())
                            page_num = int(mm.group(1))
                            break
                        else:
                            title_lines.append(l2)
                title = " ".join(title_lines).strip()
                entries.append([2, f"{chapter_label} {chnum}: {title}", page_num])
                while i < len(lines):
                    l3 = lines[i].strip()
                    if not l3:
                        i += 1
                        continue
                    if part_or_marker_re.match(l3) or combo_re.match(l3):
                        break
                    i += 1
                continue

            i += 1
        return entries

    def parse_contents(self):
        if not self.doc:
            messagebox.showwarning("توجه", "ابتدا یک PDF باز کنید.")
            return
        try:
            start = int(self.entry_start.get())
            end = int(self.entry_end.get())
        except ValueError:
            messagebox.showwarning("توجه", "شماره صفحه شروع/پایان را درست وارد کنید.")
            return

        part_kw = (self.entry_part_kw.get() or "PART").strip()
        chapter_label = (self.entry_chapter_label.get() or "Chapter").strip()

        combined = ""
        for pno in range(start, min(end, len(self.doc))):
            combined += self.doc[pno].get_text("text")

        entries = self._parse_lines(combined, part_kw, chapter_label)

        self.entries = entries
        self.trim_start_idx = None
        self.trim_end_idx = None
        self.anchor_idx = None
        self.offset = None
        self.lbl_trim.config(text="محدوده: کل جدول")
        self.lbl_anchor.config(text="Anchor: تعیین نشده")
        self.lbl_offset.config(text="افست: -")
        self.refresh_table()
        messagebox.showinfo("پارس فهرست", f"{len(entries)} ورودی پیدا شد.")

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for idx, (level, title, page) in enumerate(self.entries):
            self.tree.insert("", "end", iid=str(idx), values=(level, title, page if page is not None else ""))

    # ---------------------------------------------------------- TABLE EDIT
    def edit_cell(self, event):
        item_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item_id:
            return
        col_index = int(col.replace("#", "")) - 1
        col_name = ("level", "title", "page")[col_index]
        idx = int(item_id)
        current_val = self.entries[idx][col_index]
        new_val = simpledialog.askstring("ویرایش", f"مقدار جدید برای {col_name}:", initialvalue=str(current_val) if current_val is not None else "")
        if new_val is None:
            return
        if col_name == "level":
            try:
                self.entries[idx][0] = int(new_val)
            except ValueError:
                pass
        elif col_name == "page":
            new_val = new_val.strip()
            self.entries[idx][2] = int(new_val) if new_val else None
        else:
            self.entries[idx][1] = new_val
        self.refresh_table()

    def add_row(self):
        sel = self.tree.selection()
        insert_at = int(sel[0]) + 1 if sel else len(self.entries)
        self.entries.insert(insert_at, [2, "عنوان جدید", None])
        self.refresh_table()

    def delete_row(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        del self.entries[idx]
        self.refresh_table()

    # ---------------------------------------------------------- TRIM
    def set_trim_start(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("توجه", "ابتدا یک ردیف را انتخاب کنید.")
            return
        self.trim_start_idx = int(sel[0])
        self._update_trim_label()

    def set_trim_end(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("توجه", "ابتدا یک ردیف را انتخاب کنید.")
            return
        self.trim_end_idx = int(sel[0])
        self._update_trim_label()

    def _update_trim_label(self):
        s = self.trim_start_idx if self.trim_start_idx is not None else 0
        e = self.trim_end_idx if self.trim_end_idx is not None else len(self.entries) - 1
        self.lbl_trim.config(text=f"محدوده: ردیف {s} تا {e}")

    # ---------------------------------------------------------- ANCHOR / OFFSET
    def set_anchor(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("توجه", "ابتدا یک ردیف را انتخاب کنید.")
            return
        self.anchor_idx = int(sel[0])
        level, title, page = self.entries[self.anchor_idx]
        self.lbl_anchor.config(text=f"Anchor: {title[:50]}  (صفحه چاپی {page})")

    def auto_detect_offset(self):
        if self.anchor_idx is None:
            messagebox.showwarning("توجه", "ابتدا یک ردیف را به‌عنوان Anchor تعیین کنید.")
            return
        if not self.doc:
            return
        level, title, printed_page = self.entries[self.anchor_idx]
        if printed_page is None:
            messagebox.showwarning("توجه", "ردیف Anchor شماره صفحه چاپی ندارد.")
            return

        # search text: strip leading "Chapter N: " prefix for a cleaner match
        search_text = re.sub(r'^\S+\s+\d+:\s*', '', title).strip()
        search_text = search_text[:60]

        try:
            search_start = int(self.entry_search_start.get())
        except ValueError:
            search_start = 0

        found_page = None
        for pno in range(search_start, len(self.doc)):
            if self.doc[pno].search_for(search_text):
                found_page = pno
                break

        if found_page is None:
            messagebox.showerror("پیدا نشد", f"متن '{search_text}' در PDF (از صفحه {search_start} به بعد) پیدا نشد.\nمتن anchor یا صفحه جستجو را تنظیم کنید.")
            return

        self.offset = found_page - printed_page
        self.lbl_offset.config(text=f"افست: {self.offset}  (صفحه واقعی یافت‌شده: {found_page})")

    def apply_manual_offset(self):
        try:
            self.offset = int(self.entry_manual_offset.get())
        except ValueError:
            messagebox.showwarning("توجه", "افست دستی را به‌صورت عدد وارد کنید.")
            return
        self.lbl_offset.config(text=f"افست: {self.offset}  (دستی)")

    # ---------------------------------------------------------- BUILD OUTPUT
    def build_output(self):
        if not self.doc:
            messagebox.showwarning("توجه", "ابتدا یک PDF باز کنید.")
            return
        if not self.entries:
            messagebox.showwarning("توجه", "ابتدا فهرست را پارس کنید.")
            return
        if self.offset is None:
            messagebox.showwarning("توجه", "ابتدا افست را (خودکار یا دستی) تعیین کنید.")
            return

        s = self.trim_start_idx if self.trim_start_idx is not None else 0
        e = self.trim_end_idx if self.trim_end_idx is not None else len(self.entries) - 1
        subset = self.entries[s:e + 1]

        total_pages = len(self.doc)
        toc = []
        for level, title, printed_page in subset:
            if printed_page is None:
                continue
            pdf_page = printed_page + self.offset
            if pdf_page < 0 or pdf_page >= total_pages:
                continue
            toc.append([level, title, pdf_page + 1])  # PyMuPDF is 1-based

        if not toc:
            messagebox.showerror("خطا", "هیچ ورودی معتبری برای ساخت ایندکس پیدا نشد.")
            return
        if toc[0][0] != 1:
            toc[0][0] = 1

        default_name = os.path.splitext(os.path.basename(self.pdf_path))[0] + "_indexed.pdf"
        out_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=default_name, filetypes=[("PDF files", "*.pdf")])
        if not out_path:
            return

        def worker():
            try:
                self.doc.set_toc(toc)
                self.doc.save(out_path)
                self.root.after(0, lambda: messagebox.showinfo("انجام شد", f"فایل ذخیره شد:\n{out_path}\n\n{len(toc)} ورودی ایندکس اضافه شد."))
                self.root.after(0, lambda: self.lbl_status.config(text=f"ذخیره شد: {out_path}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("خطا", str(e)))

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = TocBuilderApp(root)
    root.mainloop()