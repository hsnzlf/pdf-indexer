<div align="center">

# 📚 PDF Indexer

### Automatically Generate PDF Bookmarks from Printed Table of Contents

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![GUI](https://img.shields.io/badge/GUI-Tkinter-success)
![Library](https://img.shields.io/badge/PDF-PyMuPDF-red)
![License](https://img.shields.io/badge/License-MIT-green)

A lightweight desktop application that automatically creates **PDF Bookmarks (Outline / TOC)** for large books using their printed **Table of Contents**.

⭐ If you find this project useful, consider giving it a star!

---

🇺🇸 **English** | [🇮🇷 فارسی](#-فارسی)

</div>

---

# ✨ Features

✅ Fully Automatic Bookmark Generation

✅ Automatic Table of Contents Detection

✅ Automatic Page Offset Calculation

✅ Automatic Chapter Matching

✅ Manual Editing Mode

✅ Multi-volume Book Support

✅ Edit/Delete/Add Bookmark Entries

✅ Simple Desktop GUI

✅ Powered by **PyMuPDF**

---

# 🎯 Perfect For

- 📖 Medical Textbooks
- 📚 Engineering Books
- 🎓 University References
- 📑 Scientific PDFs
- 📦 Multi-volume Books
- 📄 Large PDF Documents

---

# 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/hsnzlf/pdf-indexer.git
```

Go to project directory:

```bash
cd pdf-indexer
```

Install dependencies:

```bash
pip install pymupdf
```

---

# ▶️ Run

```bash
python pdf_indexer.py
```

---

# 🤖 Automatic Mode

The application automatically:

1. 📂 Opens the PDF
2. 🔍 Detects the **Contents** pages
3. 📑 Extracts chapter titles
4. 📍 Finds the real chapter locations
5. 🧮 Calculates page offset
6. 📚 Generates bookmarks
7. 💾 Saves a new indexed PDF

For most books, **no manual work is required**.

---

# 🛠 Manual Mode

For uncommon PDF layouts you can:

- 📄 Browse pages
- ✏️ Edit chapter titles
- ➕ Add bookmarks
- ❌ Delete bookmarks
- 🎯 Select anchor chapter
- 🔢 Set page offset manually
- 💾 Export indexed PDF

---

# 🖼 Screenshots

> Coming soon...

You can place screenshots here.

---

# 📂 Project Structure

```
pdf-indexer/
│
├── pdf_indexer.py
├── README.md
└── LICENSE
```

---

# 📋 Requirements

- Python 3.10+
- PyMuPDF

Install:

```bash
pip install pymupdf
```

---

# 🗺 Roadmap

- [x] Automatic bookmark generation
- [x] Manual editing mode
- [x] Automatic page offset detection
- [ ] OCR support for scanned PDFs
- [ ] Drag & Drop support
- [ ] Linux support
- [ ] macOS support
- [ ] Batch processing
- [ ] Multi-language interface

---

# 🤝 Contributing

Contributions are welcome!

If you have ideas or find bugs, feel free to:

- Open an Issue
- Submit a Pull Request
- Suggest new features

---

# ⭐ Support

If this project helps you, please consider giving it a ⭐ on GitHub.

It motivates future development.

---

# 📄 License

MIT License

Made with ❤️ by Hossein Zolfaghari

---

# 🇮🇷 فارسی

## 📚 معرفی

**PDF Indexer** یک نرم‌افزار گرافیکی سبک است که به‌صورت خودکار Bookmark (Outline) فایل‌های PDF را از روی فهرست مطالب چاپی کتاب ایجاد می‌کند.

این برنامه مخصوص کتاب‌های حجیم طراحی شده است؛ به‌ویژه کتاب‌هایی که Bookmark ندارند یا Bookmark آن‌ها ناقص است.

---

## ✨ امکانات

✅ ساخت کاملاً خودکار Bookmark

✅ تشخیص خودکار صفحات فهرست مطالب

✅ محاسبه خودکار اختلاف شماره صفحات

✅ تشخیص خودکار محل واقعی فصل‌ها

✅ حالت دستی برای فایل‌های خاص

✅ ویرایش، حذف و افزودن Bookmark

✅ پشتیبانی از کتاب‌های چندجلدی

✅ رابط کاربری ساده و سبک

---

## 🚀 نصب

ابتدا پروژه را دریافت کنید:

```bash
git clone https://github.com/hsnzlf/pdf-indexer.git
```

سپس:

```bash
cd pdf-indexer
```

وابستگی را نصب کنید:

```bash
pip install pymupdf
```

---

## ▶️ اجرا

```bash
python pdf_indexer.py
```

---

## 🤖 حالت خودکار

برنامه به‌صورت خودکار:

1. فایل PDF را باز می‌کند.
2. صفحات فهرست مطالب را پیدا می‌کند.
3. عنوان فصل‌ها را استخراج می‌کند.
4. محل واقعی فصل‌ها را پیدا می‌کند.
5. اختلاف شماره صفحات را محاسبه می‌کند.
6. Bookmarkها را ایجاد می‌کند.
7. فایل جدید را ذخیره می‌کند.

در اکثر کتاب‌ها هیچ تنظیم دستی لازم نیست.

---

## 🛠 حالت دستی

در صورت متفاوت بودن قالب کتاب می‌توانید:

- صفحات را مرور کنید.
- محدوده فهرست مطالب را انتخاب کنید.
- عنوان‌ها را ویرایش کنید.
- فصل‌ها را حذف یا اضافه کنید.
- Anchor تعیین کنید.
- Offset را دستی تنظیم کنید.
- فایل نهایی را ذخیره کنید.

---

## 📌 مناسب برای

- 📖 کتاب‌های پزشکی
- 📚 کتاب‌های مهندسی
- 🎓 منابع دانشگاهی
- 📑 مقالات و رفرنس‌ها
- 📦 کتاب‌های چندجلدی

---

## 🤝 مشارکت

اگر ایده یا پیشنهادی دارید، خوشحال می‌شوم Pull Request یا Issue ثبت کنید.

---

## ⭐ حمایت

اگر این پروژه برای شما مفید بود، لطفاً در GitHub به آن ⭐ بدهید.

این کار باعث ادامه توسعه پروژه خواهد شد.

---

## 📄 مجوز

MIT License

ساخته شده با ❤️ توسط Hossein Zolfaghari

