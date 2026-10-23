# نسخة الهاتف

هذه نسخة Kivy مستقلة للهواتف، وتستخدم منطق الشطرنج نفسه الموجود في نسخة سطح المكتب. واجهتها مبنية للمس، وتدعم اللعب ضد الكمبيوتر بثلاث صعوبات أو اللعب بين شخصين على الجهاز نفسه.

## إنشاء تطبيق Android

### تجهيز APK ونشره للتنزيل العام على GitHub (مناسب لـ Windows)

يتضمن المشروع سير عمل يبني APK على خادم Linux ويرفقه تلقائيًا بإصدار GitHub عند نشره من الموقع. لا يحتاج هذا الخيار إلى WSL أو تفعيل الافتراضية على الكمبيوتر:

1. أنشئ مستودعًا خاصًا أو عامًا على GitHub وارفع محتويات مجلد `mobile_app` إليه، بما فيها `.github/workflows/android-debug.yml`.
2. اجعل المستودع **Public** إذا أردت أن يتمكن الجميع من رؤية الإصدارات وتنزيلها.
3. افتح **Settings > Actions > General** وتأكد أن Actions مسموح بها، وأن إذن **GITHUB_TOKEN** مضبوط على **Read and write permissions** حتى يستطيع سير العمل إنشاء الإصدار.
4. افتح **Releases > Draft a new release**، وأنشئ وسمًا مثل `v0.1.0`، ثم اختر **Publish release**. سيبني GitHub التطبيق ويرفق ملف APK بالإصدار. يستغرق ذلك وقتًا؛ انتظر نجاح تشغيل **Build Android debug APK** في تبويب **Actions**.
5. بعد اكتمال البناء، افتح صفحة **Releases** ونزّل ملف APK. يستطيع اللاعبون الآخرون تنزيله من صفحة الإصدار العامة وتثبيته؛ قد يطلب Android السماح بالتثبيت من هذا المصدر.

يمكن تشغيل **Build Android debug APK** يدويًا من تبويب **Actions** للحصول على APK تجريبي (artifact)، لكنه لا يُنشر في **Releases**. اللعبة الحالية تعمل دون اتصال ضد الكمبيوتر أو بين لاعبين على الجهاز نفسه، ولا تتضمن لعبًا عبر الإنترنت.

### البناء محليًا باستخدام WSL2

إذا أردت البناء على الكمبيوتر نفسه، يتطلب Android بيئة Linux. على Windows يمكن استخدام WSL2 مع Ubuntu:

1. من إعدادات BIOS/UEFI، فعّل Intel Virtualization Technology (VT-x). يختلف اسم الإعداد ومكانه حسب الشركة المصنّعة؛ لا تغيّر إعدادات أخرى.
2. في Windows، فعّل ميزة **Virtual Machine Platform**، ثم افتح Windows Terminal بصلاحيات المسؤول وثبّت Ubuntu:

   ```powershell
   wsl --install -d Ubuntu
   ```

   أعد تشغيل Windows إذا طلب منك المثبّت ذلك، ثم أكمل إعداد حساب Ubuntu عند فتحه لأول مرة.
3. في طرفية Ubuntu، ثبّت متطلبات Buildozer وAndroid SDK/NDK وفق دليل Buildozer الرسمي، ثم انتقل إلى مجلد المشروع عبر `/mnt`:

   ```bash
   cd "/mnt/d/my folder/مشاريعي البرمجيه/mobile_app"
   ```

4. أنشئ بيئة Python وثبّت أدوات البناء:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install buildozer cython
   ```

5. أنشئ نسخة اختبار:

   ```bash
   buildozer android debug
   ```

   سيضع Buildozer ملف APK في مجلد `bin`. أول بناء قد يستغرق وقتًا لأنه ينزّل أدوات Android اللازمة.
6. انقل ملف APK إلى الهاتف عبر USB أو وسيلة نقل ملفات مناسبة، وافتحه على الهاتف لتثبيته.

لاختبار USB من الكمبيوتر بدلًا من نقل الملف يدويًا، ثبّت Android Platform Tools على Windows، فعّل **USB debugging** في الهاتف، ثم نفّذ `adb install` على ملف APK.

## النشر لاحقًا

لم يُنشأ APK أو يُنشر بعد. إصدار GitHub الذي ينتجه الإعداد أعلاه مخصص للتنزيل والتثبيت المباشر، وليس إصدار Google Play. النشر على Google Play يحتاج حساب Play Console، ومعرّف حزمة فريدًا، وملف إصدار موقّعًا بالشكل الذي يطلبه المتجر. لا ترفع ملف الاختبار على أنه إصدار المتجر.

قبل النشر، غيّر `package.domain` في `buildozer.spec` إلى معرّف حزمة فريد لا يتغير بعد النشر. أنشئ نسخة إصدار، ثم وقّعها بمفتاح نشر وفق متطلبات متجر Google Play:

```bash
buildozer android release
```

احتفظ بنسخة احتياطية آمنة من مفتاح التوقيع وكلمة مروره؛ ستحتاج إلى المفتاح نفسه لتحديث التطبيق مستقبلًا. تحقّق من صيغة الملف الناتج ومتطلبات الرفع والتوقيع الحالية في Buildozer وGoogle Play قبل النشر.

## إنشاء تطبيق iOS

يتطلب بناء iOS جهاز macOS مع Xcode؛ لا يمكن إنشاء أو توقيع ملف IPA على Windows.

1. على macOS، ثبّت Xcode وأدوات سطر الأوامر، ثم ثبّت Kivy-iOS:

   ```bash
   python3 -m pip install kivy-ios
   toolchain build python3 kivy
   ```

2. من داخل هذا المجلد أنشئ مشروع Xcode:

   ```bash
   toolchain create ChessHeroes .
   ```

3. افتح المشروع الناتج في Xcode، اختر فريق التوقيع ومعرّف الحزمة الخاصين بك، ثم أنشئ الأرشيف ووزّعه من Xcode.

## ملاحظات

- يعتمد المشروع على Python وKivy كما هو محدد في `requirements.txt` و`buildozer.spec`.
- تتضمن `assets` خطوط Noto Sans Arabic وNoto Sans Symbols 2 لإظهار العربية وقطع الشطرنج، مع ملفات الترخيص؛ أُضيفت امتدادات `ttf` و`txt` إلى قائمة الملفات المضمّنة في التطبيق.
- ملفات Android وiOS النهائية لم تُبنَ أو تُوقّع هنا؛ فبيئة العمل الحالية Windows ولا تحتوي إعدادات SDK أو شهادات نشر.
