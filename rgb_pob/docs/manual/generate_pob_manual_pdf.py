#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Arabic RTL user guide PDF for RGB POB module."""

from pathlib import Path

from weasyprint import HTML

OUT_DIR = Path(__file__).resolve().parent
OUT_PDF = OUT_DIR / "دليل_تشغيل_موديول_POB.pdf"
OUT_HTML = OUT_DIR / "دليل_تشغيل_موديول_POB.html"

CSS = """
@page {
  size: A4;
  margin: 1.6cm 1.5cm 1.8cm 1.5cm;
  @top-center {
    content: "دليل تشغيل موديول POB — Personnel on Board";
    font-family: "Noto Sans Arabic", "DejaVu Sans", sans-serif;
    font-size: 9pt;
    color: #0F4C5C;
    padding-bottom: 4pt;
    border-bottom: 1.5pt solid #0F4C5C;
  }
  @bottom-center {
    content: "صفحة " counter(page) " — RGB / Al-Abar — rgb_pob 18.0.1.0.0";
    font-family: "Noto Sans Arabic", "DejaVu Sans", sans-serif;
    font-size: 8pt;
    color: #777;
  }
}
html { direction: rtl; }
body {
  font-family: "Noto Sans Arabic", "DejaVu Sans", sans-serif;
  font-size: 11pt;
  line-height: 1.55;
  color: #1a1a1a;
}
h1 {
  color: #0F4C5C;
  font-size: 15pt;
  margin: 0 0 10pt 0;
  padding-bottom: 4pt;
  border-bottom: 2pt solid #E36414;
  page-break-after: avoid;
}
h2 {
  color: #E36414;
  font-size: 12.5pt;
  margin: 14pt 0 6pt 0;
  page-break-after: avoid;
}
h3 {
  color: #0F4C5C;
  font-size: 11.5pt;
  margin: 10pt 0 4pt 0;
}
p { margin: 0 0 6pt 0; }
.cover {
  text-align: center;
  margin-top: 4cm;
  page-break-after: always;
}
.cover h1 {
  font-size: 22pt;
  border: none;
  color: #0F4C5C;
}
.cover .sub {
  font-size: 13pt;
  color: #555;
  margin-top: 8pt;
}
.cover .meta {
  margin-top: 2cm;
  color: #777;
  font-size: 10pt;
}
.path {
  background: #E8F1F2;
  padding: 6pt 10pt;
  border-right: 4pt solid #0F4C5C;
  margin: 6pt 0 10pt 0;
}
.path b { color: #0F4C5C; }
.en {
  font-family: "DejaVu Sans", "Noto Sans Arabic", sans-serif;
  direction: ltr;
  unicode-bidi: embed;
  display: inline;
}
ol.steps {
  list-style: none;
  counter-reset: step;
  margin: 0 0 10pt 0;
  padding: 0;
}
ol.steps li {
  counter-increment: step;
  display: flex;
  gap: 8pt;
  align-items: flex-start;
  margin: 0 0 5pt 0;
  background: #F7F3E9;
  border: 0.5pt solid #d0d0d0;
  border-radius: 4pt;
  padding: 6pt 8pt;
}
ol.steps li::before {
  content: counter(step);
  flex: 0 0 22pt;
  height: 22pt;
  line-height: 22pt;
  text-align: center;
  background: #0F4C5C;
  color: #fff;
  border-radius: 50%;
  font-size: 10pt;
  font-weight: 700;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 8pt 0 12pt 0;
  font-size: 10pt;
}
th, td {
  border: 0.6pt solid #bbb;
  padding: 5pt 6pt;
  text-align: right;
  vertical-align: top;
}
th {
  background: #0F4C5C;
  color: #fff;
}
tr:nth-child(even) td { background: #f5f8f8; }
.note {
  background: #FFF8E7;
  border-right: 4pt solid #E36414;
  padding: 6pt 10pt;
  margin: 8pt 0;
}
.warn {
  background: #FDECEA;
  border-right: 4pt solid #C0392B;
  padding: 6pt 10pt;
  margin: 8pt 0;
}
.ok {
  background: #EAF7EE;
  border-right: 4pt solid #1E8449;
  padding: 6pt 10pt;
  margin: 8pt 0;
}
ul { margin: 0 0 8pt 1.2cm; padding: 0; }
li { margin: 0 0 3pt 0; }
.toc a { color: #0F4C5C; text-decoration: none; }
.section { page-break-inside: avoid; }
"""

HTML_BODY = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8"/>
  <title>دليل تشغيل موديول POB</title>
  <style>__CSS__</style>
</head>
<body>

<div class="cover">
  <h1>دليل إعداد وتشغيل موديول<br/>POB — Personnel on Board</h1>
  <p class="sub">إذن السفر / التواجد على المواقع النفطية والحفارات</p>
  <p class="sub">موديول: <span class="en">rgb_pob</span> — الإصدار 18.0.1.0.0</p>
  <p class="meta">
    شركة الآبار الدولية للخدمات النفطية<br/>
    RGB / Al-Abar<br/>
    Odoo 18
  </p>
</div>

<h1>محتويات الدليل</h1>
<ol class="toc">
  <li>ما هو الموديول؟</li>
  <li>المتطلبات قبل البدء</li>
  <li>تثبيت الموديول</li>
  <li>الصلاحيات والمجموعات</li>
  <li>إعداد البيانات الأساسية (الآبار والحفارات)</li>
  <li>تأهيل الموظفين للسفر</li>
  <li>سيناريو تجريبي كامل (من الإنشاء حتى الإغلاق)</li>
  <li>طلب تمديد الإقامة</li>
  <li>التنبيهات الذكية والـ Cron</li>
  <li>قائمة تحقق سريعة للعميل</li>
  <li>أسئلة شائعة ومشاكل متوقعة</li>
</ol>

<div class="section">
<h1>1) ما هو الموديول؟</h1>
<p>
موديول <span class="en">POB (Personnel on Board)</span> يدير أذونات سفر الموظفين إلى المواقع النفطية والحفارات،
مع مسار موافقات واضح، وتنبيه قبل انتهاء المدة، وإمكانية طلب تمديد الإقامة.
</p>
<table>
  <tr><th>العنصر</th><th>الوصف</th></tr>
  <tr><td>طلب POB</td><td>سجل واحد لكل موظف (رقم تسلسلي تلقائي مثل <span class="en">POB-2026-0001</span>)</td></tr>
  <tr><td>مسار الموافقة</td><td>مسودة ← انتظار العمليات ← انتظار HSE/الحقل ← نشط بالموقع ← منتهي/مغلق</td></tr>
  <tr><td>التمديد</td><td>مسار منفصل من حالة «نشط» بموافقة العمليات فقط</td></tr>
  <tr><td>التنبيه</td><td>قبل 4 أيام من تاريخ الانتهاء (نشاط + بريد + إشعار داخل النظام)</td></tr>
</table>
</div>

<div class="section">
<h1>2) المتطلبات قبل البدء</h1>
<ul>
  <li>Odoo 18 مع تطبيق الموارد البشرية <span class="en">Employees (hr)</span> و <span class="en">Discuss / mail</span>.</li>
  <li>وجود الموديول في مسار الإضافات: <span class="en">projects/Al-Abar-Al-Doulia-Oil-Services/rgb_pob</span></li>
  <li>صلاحية مسؤول النظام لتثبيت الموديولات وإدارة المستخدمين.</li>
  <li>موظفون مسجّلون في النظام للاختبار.</li>
</ul>
</div>

<div class="section">
<h1>3) تثبيت الموديول</h1>
<ol class="steps">
  <li>
    <div>
      <b>حدّث قائمة التطبيقات</b><br/>
      Apps ← Update Apps List
    </div>
  </li>
  <li>
    <div>
      <b>ابحث عن الموديول</b><br/>
      ابحث عن: <span class="en">RGB POB</span> أو <span class="en">Personnel on Board</span>
    </div>
  </li>
  <li>
    <div>
      <b>ثبّت</b><br/>
      اضغط <span class="en">Install</span> وانتظر اكتمال التثبيت.
    </div>
  </li>
  <li>
    <div>
      <b>تحقق من ظهور القائمة</b><br/>
      يجب ظهور قائمة رئيسية باسم <b>POB</b> في الشريط العلوي/الجانبي.
    </div>
  </li>
</ol>
<div class="path">
  <b>بديل سطر الأوامر (للمطور):</b><br/>
  <span class="en">odoo-bin -c &lt;config&gt; -d &lt;database&gt; -i rgb_pob --stop-after-init</span>
</div>
<div class="ok">
  بعد التثبيت قد تظهر بيانات تجريبية بسيطة: بئر <span class="en">K144</span> وحفارة <span class="en">w564</span>.
</div>
</div>

<div class="section">
<h1>4) الصلاحيات والمجموعات</h1>
<p>من: Settings ← Users &amp; Companies ← Users ← اختر المستخدم ← قسم <span class="en">POB (Personnel on Board)</span></p>
<table>
  <tr><th>المجموعة</th><th>ماذا تستطيع؟</th><th>لمن تُمنح؟</th></tr>
  <tr><td>User</td><td>إنشاء ومتابعة طلبات POB</td><td>من يُدخل الطلبات</td></tr>
  <tr><td>Operations</td><td>موافقة مرحلة العمليات + موافقة/رفض التمديد</td><td>مسؤول العمليات</td></tr>
  <tr><td>HSE / Rig</td><td>موافقة مرحلة الأمن والسلامة / الحقل</td><td>HSE أو مسؤول الحقل</td></tr>
  <tr><td>Site Supervisor</td><td>طلب تمديد الإقامة للتصاريح النشطة</td><td>مشرف الموقع</td></tr>
  <tr><td>Manager</td><td>كل الصلاحيات + إعداد الآبار/الحفارات</td><td>مدير الموديول / المسؤول</td></tr>
</table>
<div class="note">
  للاختبار السريع: امنح مستخدمًا واحدًا مجموعة <b>Manager</b> ليتمكن من تنفيذ كل الخطوات بنفسه.
</div>
</div>

<div class="section">
<h1>5) إعداد البيانات الأساسية</h1>
<h2>5.1 الآبار (Wells)</h2>
<div class="path"><b>المسار:</b> POB ← Configuration ← Wells</div>
<ol class="steps">
  <li><div>أنشئ بئرًا جديدًا (مثال: <span class="en">K144</span>)</div></li>
  <li><div>أدخل الاسم والكود (اختياري) والعميل إن لزم</div></li>
  <li><div>احفظ السجل</div></li>
</ol>

<h2>5.2 الحفارات / المواقع (Rigs)</h2>
<div class="path"><b>المسار:</b> POB ← Configuration ← Rigs</div>
<ol class="steps">
  <li><div>أنشئ حفارة جديدة (مثال: <span class="en">w564</span>)</div></li>
  <li><div>اربطها بالبئر المناسب</div></li>
  <li><div>احفظ السجل</div></li>
</ol>
<div class="note">
  عند إنشاء طلب POB سيتم فلترة الحفارات حسب البئر المختار.
</div>
</div>

<div class="section">
<h1>6) تأهيل الموظفين للسفر</h1>
<p>
لا يظهر الموظف في قائمة طلب POB إلا إذا كان مؤهلاً للسفر للمواقع النفطية.
</p>
<div class="path"><b>المسار:</b> Employees ← افتح الموظف ← تبويب Settings</div>
<ol class="steps">
  <li><div>فعّل الخيار: <b>Available for Oil Site Travel</b> (متاح للسفر للمواقع النفطية)</div></li>
  <li><div>احفظ الموظف</div></li>
</ol>
<div class="warn">
  إذا لم يظهر الموظف عند إنشاء الطلب، تأكد من تفعيل هذا الخيار.
</div>
</div>

<div class="section">
<h1>7) سيناريو تجريبي كامل</h1>
<p>اتبع هذا المثال خطوة بخطوة لتجربة النظام من البداية للنهاية.</p>

<h2>الخطوة أ — إنشاء الطلب (مسودة)</h2>
<div class="path"><b>المسار:</b> POB ← Operations ← POB Requests ← New</div>
<ol class="steps">
  <li><div>اختر الموظف المؤهل</div></li>
  <li><div>اختر البئر ثم الحفارة</div></li>
  <li><div>أدخل المدة بالأيام (مثال: 15)</div></li>
  <li><div>حدد تاريخ البداية (اليوم أو تاريخ السفر)</div></li>
  <li><div>لاحظ أن رقم الطلب يُولَّد تلقائيًا، وتاريخ الانتهاء يُحسب تلقائيًا</div></li>
  <li><div>اضغط <span class="en">Submit</span></div></li>
</ol>
<div class="ok">الحالة تصبح: <b>Pending Operations</b></div>

<h2>الخطوة ب — موافقة العمليات</h2>
<ol class="steps">
  <li><div>ادخل بمستخدم لديه مجموعة Operations (أو Manager)</div></li>
  <li><div>افتح الطلب واضغط <span class="en">Approve Operations</span></div></li>
</ol>
<div class="ok">الحالة تصبح: <b>Pending HSE / Rig</b></div>

<h2>الخطوة ج — موافقة HSE / الحقل</h2>
<ol class="steps">
  <li><div>ادخل بمستخدم لديه مجموعة HSE / Rig (أو Manager)</div></li>
  <li><div>اضغط <span class="en">Approve HSE / Rig</span></div></li>
</ol>
<div class="ok">الحالة تصبح: <b>Active / Onboard</b> — الموظف يُعتبر متواجدًا في الموقع</div>

<h2>الخطوة د — الرفض (اختياري للتجربة)</h2>
<p>
في مرحلتي Pending Operations أو Pending HSE يمكن الضغط على <span class="en">Reject</span>
ليعود الطلب إلى <b>Draft</b> مع إمكانية التعديل وإعادة الإرسال.
</p>

<h2>ملخص الحالات</h2>
<table>
  <tr><th>الحالة</th><th>المعنى</th><th>الإجراء التالي</th></tr>
  <tr><td>Draft</td><td>مسودة قابلة للتعديل</td><td>Submit</td></tr>
  <tr><td>Pending Operations</td><td>بانتظار العمليات</td><td>Approve Operations / Reject</td></tr>
  <tr><td>Pending HSE / Rig</td><td>بانتظار HSE/الحقل</td><td>Approve HSE / Reject</td></tr>
  <tr><td>Active / Onboard</td><td>نشط في الموقع</td><td>Request Extension أو الانتظار حتى الانتهاء</td></tr>
  <tr><td>Under Extension</td><td>طلب تمديد قيد الاعتماد</td><td>Approve / Reject Extension</td></tr>
  <tr><td>Expired / Closed</td><td>انتهت المدة وأُغلق تلقائيًا</td><td>—</td></tr>
</table>
</div>

<div class="section">
<h1>8) طلب تمديد الإقامة</h1>
<p>يُستخدم عندما يحتاج الموظف أيامًا إضافية وهو ما زال في حالة Active / Onboard.</p>
<ol class="steps">
  <li>
    <div>
      افتح الطلب النشط بمستخدم <b>Site Supervisor</b> أو <b>Manager</b>
    </div>
  </li>
  <li>
    <div>
      اضغط <span class="en">Request Extension</span>
    </div>
  </li>
  <li>
    <div>
      أدخل عدد الأيام الإضافية (مثال: 5) وسبب التمديد (إلزامي) ثم Submit Extension
    </div>
  </li>
  <li>
    <div>
      الحالة تصبح <b>Under Extension</b> وتُقفل الحقول الأساسية
    </div>
  </li>
  <li>
    <div>
      مستخدم Operations يضغط <span class="en">Approve Extension</span>
      (أو Reject Extension للرفض دون تغيير المدة)
    </div>
  </li>
</ol>
<div class="ok">
  عند الموافقة: يعود الطلب إلى Active، ويُحدَّث تاريخ الانتهاء، ويُعاد ضبط التنبيه (قبل 4 أيام من التاريخ الجديد).
</div>
</div>

<div class="section">
<h1>9) التنبيهات الذكية والـ Cron</h1>
<ul>
  <li>قبل <b>4 أيام</b> من تاريخ الانتهاء يرسل النظام تنبيهًا تلقائيًا لمستخدمي Operations/Manager.</li>
  <li>قنوات التنبيه: نشاط (Activity) + بريد إلكتروني + إشعار داخل Odoo.</li>
  <li>في قائمة الطلبات يظهر تلوين تحذيري عند اقتراب الانتهاء.</li>
  <li>عند تجاوز تاريخ الانتهاء والطلب ما زال Active: يُغلق تلقائيًا إلى Expired / Closed.</li>
</ul>
<div class="path">
  <b>مراقبة الـ Cron:</b> Settings ← Technical ← Automation ← Scheduled Actions<br/>
  ابحث عن: <span class="en">POB: Expiry Alerts &amp; Auto Close</span>
</div>
<div class="note">
  للتجربة السريعة يمكن تشغيل الإجراء المجدول يدويًا (Run Manually) بعد ضبط تاريخ انتهاء قريب على طلب تجريبي.
</div>
</div>

<div class="section">
<h1>10) قائمة تحقق سريعة للعميل</h1>
<table>
  <tr><th>#</th><th>الإجراء</th><th>تم؟</th></tr>
  <tr><td>1</td><td>تثبيت <span class="en">rgb_pob</span> وظهور قائمة POB</td><td>☐</td></tr>
  <tr><td>2</td><td>منح الصلاحيات للمستخدمين التجريبيين</td><td>☐</td></tr>
  <tr><td>3</td><td>إنشاء بئر وحفارة</td><td>☐</td></tr>
  <tr><td>4</td><td>تفعيل أهلية السفر لموظف</td><td>☐</td></tr>
  <tr><td>5</td><td>إنشاء طلب POB وإرساله</td><td>☐</td></tr>
  <tr><td>6</td><td>موافقة العمليات ثم HSE ووصوله لـ Active</td><td>☐</td></tr>
  <tr><td>7</td><td>طلب تمديد وموافقة العمليات</td><td>☐</td></tr>
  <tr><td>8</td><td>التحقق من تحديث تاريخ الانتهاء</td><td>☐</td></tr>
  <tr><td>9</td><td>مراجعة قائمة Active Onboard والفلاتر</td><td>☐</td></tr>
</table>
</div>

<div class="section">
<h1>11) أسئلة شائعة ومشاكل متوقعة</h1>
<table>
  <tr><th>المشكلة</th><th>الحل</th></tr>
  <tr>
    <td>لا تظهر قائمة POB</td>
    <td>تأكد من تثبيت الموديول ومنح المستخدم مجموعة User على الأقل، ثم حدّث الصفحة.</td>
  </tr>
  <tr>
    <td>الموظف غير موجود في القائمة</td>
    <td>فعّل <span class="en">Available for Oil Site Travel</span> على بطاقة الموظف.</td>
  </tr>
  <tr>
    <td>لا تظهر الحفارة</td>
    <td>اربط الحفارة بالبئر المختار في الطلب، وتأكد أنها Active.</td>
  </tr>
  <tr>
    <td>زر التمديد غير ظاهر</td>
    <td>الطلب يجب أن يكون Active، والمستخدم في مجموعة Supervisor أو Manager.</td>
  </tr>
  <tr>
    <td>لا تصل إيميلات التنبيه</td>
    <td>اضبط خادم البريد في Settings ← Technical ← Email، وتأكد أن للمستخدمين بريدًا صحيحًا.</td>
  </tr>
  <tr>
    <td>لا يمكن تعديل الحقول بعد الإرسال</td>
    <td>هذا متعمد: الحقول الأساسية تُقفل بعد Draft. استخدم Reject للعودة للمسودة أو اطلب تمديدًا للحالة النشطة.</td>
  </tr>
</table>
</div>

<div class="section">
<h1>خاتمة</h1>
<p>
بهذا الدليل يمكن للعميل تثبيت الموديول، ضبط الصلاحيات والبيانات، وتنفيذ سيناريو كامل:
إنشاء إذن سفر ← موافقتان ← تواجد نشط ← تمديد ← إغلاق تلقائي عند انتهاء المدة.
</p>
<div class="ok">
  للدعم الفني: راجع سجلات Chatter داخل طلب POB، والأنشطة المجدولة، وقوالب البريد الخاصة بالموديول.
</div>
</div>

</body>
</html>
"""


def main():
    html = HTML_BODY.replace("__CSS__", CSS)
    OUT_HTML.write_text(html, encoding="utf-8")
    HTML(string=html, base_url=str(OUT_DIR)).write_pdf(OUT_PDF)
    print(f"Wrote: {OUT_PDF}")
    print(f"Also: {OUT_HTML}")


if __name__ == "__main__":
    main()
