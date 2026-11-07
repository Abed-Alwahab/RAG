# 🎓 المرشد الأكاديمي الذكي | AAUP Smart Academic Advisor

نظام أسئلة وأجوبة أكاديمي يعتمد على **Retrieval-Augmented Generation (RAG)** لاسترجاع معلومات من وثائق الجامعة العربية الأمريكية والإجابة بالعربية مع الإشارة إلى المصادر والصفحات.

## المتطلبات
- Python 3.11 أو 3.12 (موصى به؛ التوافق يعتمد على إصدارات الحزم والمنصة).
- اتصال إنترنت لتحميل نموذج التضمين لأول مرة ولاستخدام Gemini.
- مفتاح Gemini API صالح مع صلاحية الوصول للنموذج المعرّف في `rag.py`.
- مساحة تخزين وذاكرة كافيتان لتنزيل نموذج Sentence Transformers.

## التثبيت (Windows PowerShell)
```powershell
cd Academic-Advisor-Ready
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```
افتح `.env` وضع مفتاحك الحقيقي بدل `replace_with_your_gemini_api_key`. **لا تشارك ملف `.env`**.

## التثبيت (macOS / Linux)
```bash
cd Academic-Advisor-Ready
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```
عدّل `.env` وأدخل مفتاحك.

## التشغيل السريع
تتضمن الحزمة قاعدة `vectorstore_v3` جاهزة للتجربة؛ لا يلزم إعادة الفهرسة في البداية. من مجلد المشروع:
```bash
streamlit run app.py
```
افتح الرابط المحلي الذي يعرضه Streamlit (عادة `http://localhost:8501`). يمكن أيضاً اختبار الواجهة النصية:
```bash
python rag.py
```
**مهم:** إذا ظهر خطأ `404 NOT_FOUND` أو `503 UNAVAILABLE` من Gemini، تحقق من توفر النموذج في حسابك وعدّل `MODEL_NAME` داخل `rag.py` إلى نموذج متاح فعلاً. 401 يدل عادة على مشكلة في المفتاح أو المصادقة. لم يتم اختبار اتصال API حيّ أثناء إعداد الحزمة.

## إعادة بناء قاعدة المعرفة (اختياري)
المجلد `data/` يحتوي على الوثائق المرجعية. ملف `ocr_output.txt` يوفر النص المستخرج من دليل الطالب المستخدم في المشروع. لإعادة بناء الفهرس:
```bash
python vector_store.py
```
**تنبيه:** الأمر يحذف `vectorstore_v3` الحالية ويعيد إنشاءها؛ احتفظ بنسخة احتياطية قبل تشغيله. يعتمد `ingest.py` على وجود `ocr_output.txt` لدليل الطالب.

## استخراج النصوص من ملفات PDF باستخدام Unstructured وOCR

يستخدم المشروع مسارين لاستخراج محتوى الوثائق الأكاديمية:

1. **PyMuPDF**: استخراج النص المباشر من ملفات PDF التي تحتوي على طبقة نص قابلة للقراءة، مع الاحتفاظ باسم المستند ورقم الصفحة.
2. **Unstructured + OCR**: معالجة دليل الطالب `Student-Guide-2024-2025-Ar.pdf` باستخدام `partition_pdf(strategy="ocr_only", languages=["ara", "eng"])` في `test_ocr.py`. يُقسّم السكربت الملف إلى صفحات مؤقتة، ثم يجري OCR بالعربية والإنجليزية، ويسجّل حالة كل صفحة (`SUCCESS` / `EMPTY` / `FAILED`) ويحفظ الناتج في `ocr_output.txt`.

يقرأ `ingest.py` النص المستخرج مسبقاً من `ocr_output.txt`، ويسجّل `method="unstructured_ocr"` مع مصدر المستند ورقم الصفحة؛ أما الملفات النصية الأخرى فتُقرأ عبر PyMuPDF مع `method="pymupdf"`. بعد ذلك تُقسّم النصوص إلى مقاطع ويُنشأ فهرس ChromaDB لاسترجاع المعلومات أثناء الإجابة. **لا يُنفّذ OCR عند كل سؤال**، وملف `ocr_output.txt` مرفق بالفعل.

### متطلبات OCR الإضافية

- تثبيت Python packages عبر `requirements.txt` الذي يشمل `unstructured[pdf]` إلى جانب جميع مكتبات تشغيل الموقع والـRAG.
- يلزم تثبيت **Tesseract OCR** على نظام التشغيل، وإتاحة الأمر `tesseract` عبر PATH، وتثبيت بيانات اللغتين **Arabic (`ara`)** و**English (`eng`)**. بعض وظائف معالجة PDF في Unstructured قد تحتاج أيضاً **Poppler** (`pdfinfo` و`pdftoppm`) حسب النظام وطريقة المعالجة.
- على Windows يمكن تثبيت Tesseract وPoppler كلٌ على حدة وإضافة مجلدات البرامج إلى PATH. للتحقق:

```powershell
tesseract --version
tesseract --list-langs
pdfinfo -v
```

يجب أن تظهر `ara` و`eng` في قائمة لغات Tesseract. في حال فشل OCR، راجع توفر هذه البرامج ولغات OCR؛ **pip وحده لا يثبت بالضرورة البرامج الخارجية**.

لإعادة استخراج النص من دليل الطالب (اختياري، وقد يستغرق وقتاً):

```powershell
python test_ocr.py
```

ثم لإعادة بناء الفهرس (بعد أخذ نسخة احتياطية من `vectorstore_v3`):

```powershell
python vector_store.py
```

**للمحكّم:** لتشغيل الواجهة وتجربة الأسئلة باستخدام الفهرس ونتيجة OCR المرفقين، لا يلزم إعادة OCR ولا تثبيت Tesseract/Poppler. إذا كان المطلوب اختبار معالجة PDF من الصفر، فيجب تثبيت متطلبات النظام المذكورة.

### تثبيت أخف لتشغيل الواجهة فقط

`requirements.txt` هو **الملف الشامل** لجميع مكتبات Python المستخدمة في المشروع، بما فيها OCR. إذا أراد المحكّم تجربة الموقع فقط دون إعادة معالجة PDF، يمكن استخدام `requirements-core.txt` لتثبيت حزم التشغيل الأساسية دون حزم OCR الثقيلة:

```powershell
python -m pip install -r requirements-core.txt
```

## معمارية النظام
```text
طالب → Streamlit (app.py) → ask_rag (rag.py)
                               ↓
                  Hybrid Retrieval (search.py)
                    ↙                   ↘
           Semantic Search        Keyword Search
                    ↘                   ↙
                      RRF Ranking
                           ↓
                  ChromaDB vectorstore_v3
                           ↓
                  سياق من الصفحات المختارة
                           ↓
                  Gemini Interactions API
                           ↓
                   إجابة + مرجع الصفحات
```
**إعداد الفهرس:** `data/` → (`PyMuPDF` أو `Unstructured + OCR` → `ocr_output.txt`) → `ingest.py` → `chunking.py` → `vector_store.py` → ChromaDB.

## ملفات المشروع
| الملف | الوظيفة |
|---|---|
| `app.py` | واجهة المحادثة عبر Streamlit |
| `rag.py` | إعداد السياق وإرسال الطلب إلى Gemini |
| `search.py` | استرجاع هجين ودمج النتائج باستخدام RRF |
| `ingest.py` | قراءة ملفات PDF والنص المستخرج OCR |
| `chunking.py` | تقسيم النصوص إلى مقاطع |
| `vector_store.py` | إنشاء قاعدة ChromaDB |
| `vectorstore_v3/` | الفهرس المستخدم عند التشغيل |
| `data/` | وثائق PDF المرجعية |
| `sample_questions.txt` | أسئلة تجريبية |
| `.env.example` | نموذج إعداد المتغيرات |
| `requirements.txt` | جميع اعتماديات Python بما فيها Unstructured OCR |
| `requirements-core.txt` | اعتماديات التشغيل الأساسية بدون حزم OCR الثقيلة |
| `test_ocr.py` | استخراج النص من دليل الطالب عبر Unstructured وOCR |
| `ocr_output.txt` | النص المستخرج مسبقاً مع حالات الصفحات |

## اختبار التسليم للمحكّم
1. فك ضغط الحزمة في مسار قصير ويفضل بدون رموز خاصة.
2. أنشئ بيئة Python وثبّت الحزم.
3. انسخ `.env.example` إلى `.env` وأدخل مفتاحاً صالحاً.
4. نفّذ `streamlit run app.py`.
5. جرّب الأسئلة في `sample_questions.txt`، وافحص الاستشهادات مع الوثائق الأصلية.
6. للتحقق من الفهرس: `python search.py`، ثم اطرح سؤالاً وأدخل `exit` للخروج.

## القيود الحالية
- الواجهة الحالية **Streamlit** وليست Frontend منفصلاً ولا يوجد نظام حسابات طلاب.
- يلزم مفتاح Gemini متاح، وقد تختلف إتاحة النموذج حسب الحساب.
- قد يحتاج تثبيت المكتبات إلى وقت وتنزيلات كبيرة أول مرة.
- البحث يستند إلى الوثائق المفهرسة فقط؛ راجع النتائج مع تعليمات الجامعة الرسمية.
- لا تُخزّن مفاتيح API في Git أو في النسخ المشتركة.
- لم يتم إجراء اختبار تشغيل كامل على جهاز المحكّم أو اختبار حيّ لاتصال Gemini.

## تشغيل سريع للمحكّم — Windows
من PowerShell داخل المجلد الذي يحتوي على `app.py`:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# افتح .env وضع مفتاح Gemini الخاص بك
.\.venv\Scripts\python.exe check_setup.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

يمكن استخدام `RUN_WINDOWS.ps1` لتثبيت الاعتماديات وتشغيل الواجهة (بعد إعداد `.env`).

### فحص ما قبل العرض
`python check_setup.py` يتحقق من وجود الملفات والوثائق والفهرس، ومن تركيب ملفات Python والحزم وإعداد المفتاح، دون إرسال طلب إلى Gemini. نجاح الفحص **لا يضمن** نجاح الاتصال بالخدمة؛ جرّب سؤالاً فعلياً في الواجهة.

### بيانات التجربة
- `data/`: ثلاثة ملفات PDF مرجعية مرفقة من نسخة المشروع المرسلة.
- `ocr_output.txt`: النص المستخرج مسبقاً لدليل الطالب.
- `vectorstore_v3/`: فهرس ChromaDB جاهز؛ لا تعِد إنشاءه للتجربة الأولية.
- `sample_questions.txt`: أسئلة تجريبية، منها سؤال خارج نطاق الوثائق لاختبار رفض الإجابة غير المدعومة.

### تنبيهات خاصة بالنسخة الحالية
- إعداد النموذج موجود في `rag.py` في المتغير `MODEL_NAME`، والقيمة الحالية `gemini-3.6-flash`؛ تحقق من إتاحة هذا الاسم لحسابك قبل العرض.
- لا تُرفق `.env` بمفتاح حقيقي في التسليم. المحكّم يحتاج إلى مفتاح صالح خاص به، أو بيئة اختبار آمنة مجهّزة مسبقاً.
- يعتمد التشغيل على تنزيل نموذج embedding أول مرة، لذلك يتطلب إنترنت عند أول تشغيل.
- عند تشغيل الأوامر من خارج مجلد المشروع قد لا يُعثر على قاعدة البيانات بسبب المسارات النسبية.