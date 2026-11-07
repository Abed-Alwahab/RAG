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
**إعداد الفهرس:** `data/` → `ingest.py` → `chunking.py` → `vector_store.py` → ChromaDB.

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
| `requirements.txt` | اعتماديات Python |

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