<div dir="rtl">

# لیست باگ‌ها و کارهای باقی‌مانده (TODO)

این فایل شامل تمامی باگ‌ها، ناسازگاری‌ها و نواقص شناسایی‌شده در کل سیستم (بر اساس بررسی کدها، خروجی `xacro`، لاگ‌های اجرای Gazebo و نتایج `colcon test`) است.

---

## ۱. باگ‌های بحرانی (فیزیک Gazebo، برخورد و Xacro)

### ۱.۱. حذف شدن کامل Collisionهای ربات و ۳ آبجکت در Gazebo Harmonic (`dartsim`)
- **محل باگ:**
  - ربات: `nova_description/urdf/mech/nova.urdf.xacro` (خطوط ۷۹–۸۴، ۱۰۲–۱۰۷، ۱۳۰–۱۳۵، ۱۵۸–۱۶۳، ۱۸۶–۱۹۱، ۲۱۴–۲۱۹، ۲۴۲–۲۴۷)
  - آبجکت‌ها: `models/mustard/model.sdf` (خطوط ۱۴–۲۱)، `models/cheezit_big_original/model.sdf` (خطوط ۲۸–۳۴)، `models/coke_can/model.sdf` (خطوط ۱۷–۲۳) در پکیج `nova_gazebo`
- **شرح باگ:** موتور فیزیک پیش‌فرض Gazebo Harmonic (`dartsim`) از ساخت Collision Geometry به صورت مستقیم از فایل مش (`.STL` / `.dae`) پشتیبانی نمی‌کند. در لاگ اجرا (`run_20261127_024533/console.log` خطوط ۲۲۹–۲۴۸) برای تمام ۷ لینک ربات (`nova_base` و `nova_link1`..`nova_link6`) و ۳ آبجکت ذکرشده خطای `Mesh construction from an SDF has not been implemented yet for dartsim` و `The geometry element of collision [...] couldn't be created` ثبت شده است. در نتیجه ربات و این ۳ آبجکت **هیچ برخورد فیزیکی ندارند** و از هم یا از زمین عبور می‌کنند.
- **راه‌حل:**
  - [ ] جایگزینی `<collision>`های مش `.STL` لینک‌های ربات در `nova.urdf.xacro` با اشکال هندسی ساده (Primitive Shapes مثل `cylinder` / `box` / `sphere`) متناسب با ابعاد لینک‌ها.
  - [ ] جایگزینی `<collision>`های مش `.dae` در `mustard/model.sdf`، `cheezit_big_original/model.sdf` و `coke_can/model.sdf` با اشکال ساده (`box` / `cylinder`).

### ۱.۲. خطای `Undefined substitution argument robot_name` هنگام پردازش مستقیم `nova.urdf.xacro`
- **محل باگ:** `nova_description/urdf/mech/nova.urdf.xacro` (خط ۲ در برابر خط ۵)
- **شرح باگ:** در خط ۲ از `$(arg robot_name)` در تگ `<robot name="$(arg robot_name)">` استفاده شده، در حالی که `<xacro:arg name="robot_name" default="nova"/>` در خط ۵ تعریف شده است. اجرای مستقیم `xacro nova.urdf.xacro` بدون ارسال آرگومان با کد خطای ۲ (`Undefined substitution argument robot_name`) متوقف می‌شود.
- **راه‌حل:**
  - [ ] بررسی و اصلاح ترتیب/استفاده از `robot_name` در `nova.urdf.xacro` (در Xacro نام ربات در تگ `<robot>` را به صورت ثابت بگذارید یا پیش از ارزیابی آدرس‌دهی نشود، و تست اجرای مستقیم `xacro nova.urdf.xacro` بدون آرگومان انجام شود).

### ۱.۳. مسیر پیش‌فرض ناموجود `controllers_file` در `nova.urdf.xacro`
- **محل باگ:** `nova_description/urdf/mech/nova.urdf.xacro` (خط ۱۲)
- **شرح باگ:** مقدار پیش‌فرض `controllers_file` به `$(find nova_moveit_config)/config/nova/ros2_controllers.yaml` اشاره می‌کند، در حالی که تنها فایل `ros2_controllers_template.yaml` در این مسیر وجود دارد و `ros2_controllers.yaml` اصلاً وجود ندارد. اگر `nova.urdf.xacro` با `use_gazebo:=true` خارج از `robot_state_publisher.launch.py` استفاده شود، پلاگین `gz_ros2_control` فایل کنترلر را پیدا نخواهد کرد.
- **راه‌حل:**
  - [ ] ایجاد یک فایل پیش‌فرض معتبر یا اطمینان از همگام‌سازی مکانیزم تولید `ros2_controllers.yaml` در پکیج مناسب (`nova_moveit_config` یا `nova_bringup`).

### ۱.۴. نبود پلاگین `<hardware>` جایگزین هنگام `use_gazebo:=false`
- **محل باگ:** `nova_description/urdf/control/nova_ros2_control.urdf.xacro` (خطوط ۱۷–۲۱)
- **شرح باگ:** بلوک `<hardware>` فقط دارای `<xacro:if value="${use_gazebo}">` است. وقتی `use_gazebo:=false` باشد، تگ `<hardware>` کاملاً خالی تولید می‌شود که هنگام اجرای `ros2_control` روی سخت‌افزار واقعی یا `mock_components/GenericSystem` (برای MoveIt بدون Gazebo) باعث خطا می‌شود.
- **راه‌حل:**
  - [ ] افزودن حالت غیر-Gazebo (مثلاً `use_fake_hardware` / `mock_components/GenericSystem` یا پلاگین درایور واقعی) داخل `<xacro:unless value="${use_gazebo}">`.

---

## ۲. باگ‌های شبیه‌سازی Gazebo، World و مدل‌ها (`nova_gazebo`)

### ۲.۱. اسپان شدن ربات به صورت معلق (`z = 0.05`)
- **محل باگ:** `nova_gazebo/launch/nova.gazebo.launch.py` (خط ۱۹۴)
- **شرح باگ:** مقدار پیش‌فرض آرگومان `z` برابر `0.05` متر است، در حالی که `ground_plane` روی `z = 0.0` قرار دارد و `nova_base.STL` از `z = 0.0` شروع می‌شود و پایه ربات به `world` فیکس شده است. در نتیجه ربات ۵ سانتی‌متر در هوا معلق می‌ماند.
- **راه‌حل:**
  - [ ] تغییر پیش‌فرض `z` به `0.0` (یا اضافه کردن میز/پایه در World متناسب با ارتفاع مورد نظر).

### ۲.۲. ایرادات متعدد مدل `mustard` در `pick_and_place_demo.world`
- **محل باگ:**
  - `nova_gazebo/models/mustard/model.sdf` (خطوط ۴، ۹، ۱۷)
  - `nova_gazebo/models/mustard/materials/scripts/mustard.material` (خط ۱)
  - `nova_gazebo/worlds/pick_and_place_demo.world` (خط ۹۱)
- **شرح باگ:**
  1. مدل با `<static>true</static>` تعریف شده و هیچ تگ `<inertial>` ندارد؛ بنابراین در سناریوی Pick and Place اصلاً قابل برداشتن و جابه‌جایی نیست.
  2. ابعاد مش `mustard.dae` (بازه `y` از `-8.0` تا `+8.0` متر و `z` از `-2.43` تا `+2.43` متر) با `<scale>0.05</scale>` طولی حدود **۸۰ سانتی‌متر** و ارتفاع **۲۴ سانتی‌متر** ایجاد می‌کند که بیش از حد بزرگ است.
  3. در `pick_and_place_demo.world` با `z = 0.08` اسپان شده، در حالی که نصف ارتفاع آن `0.12` متر است و بخش پایینی آن (`z = -0.04`) داخل زمین فرو می‌رود.
  4. فایل `mustard.material` یک اسکریپت قدیمی OGRE 1 با نام Placeholder اشتباه `material @HERE@` و نام بافت نامرتبط `optimized_tsdf_texture_mapped_mesh.png` دارد که در موتور `ogre2` گازیبو هارمونیک بی‌اثر است.
- **راه‌حل:**
  - [ ] تغییر `<static>` به `false`، افزودن `<inertial>` صحیح، اصلاح مقیاس (`scale`) و مختصات `pose` در world، اصلاح collision و پاک‌سازی/به‌روزرسانی متریال.

### ۲.۳. ناهماهنگی شعاع و ممان اینرسی بسیار اشتباه در `red_cylinder`
- **محل باگ:** `nova_gazebo/models/red_cylinder/model.sdf` (خطوط ۹–۱۵، ۲۰، ۵۸)
- **شرح باگ:**
  1. شعاع collision برابر `0.015` متر است اما شعاع visual برابر `0.0125` متر (اختلاف ۲.۵ میلی‌متر).
  2. ممان اینرسی برای استوانه‌ای با جرم `0.05 kg` و طول `0.35 m` برابر `ixx = iyy = 2.04e-7` و `izz = 3.9e-8` وارد شده است که حدود **۲۵۰۰ برابر کوچک‌تر** از مقدار واقعی (`ixx = iyy ≈ 5.13e-4`, `izz ≈ 5.63e-6`) است و باعث ناپایداری فیزیکی هنگام تماس می‌شود.
- **راه‌حل:**
  - [ ] یکسان‌سازی شعاع visual و collision و محاسبه مجدد تانسور اینرسی واقعی استوانه.

### ۲.۴. وابستگی اینترنتی `Sun` و فایل‌های قدیمی در `pick_and_place_demo.world` و `coke_can`
- **محل باگ:**
  - `nova_gazebo/worlds/pick_and_place_demo.world` (خطوط ۴۰–۴۴)
  - `nova_gazebo/models/coke_can/` (`model-1_2.sdf`، `model-1_3.sdf`، `model-1_4.sdf`)
- **شرح باگ:** نور خورشید (`Sun`) از طریق آدرس اینترنتی `https://fuel.gazebosim.org/1.0/OpenRobotics/models/Sun` لود می‌شود که در اجرای آفلاین یا اختلال شبکه باعث تاخیر/خطا در شروع Gazebo می‌شود. همچنین در `coke_can` فایل‌های SDF قدیمی و منسوخ (SDF 1.2 تا 1.4) باقی مانده‌اند.
- **راه‌حل:**
  - [ ] جایگزینی `<include>` خورشید با تعریف محلی `<light type="directional" name="sun">` در فایل `.world`.
  - [ ] پاک‌سازی فایل‌های اضافی قدیمی در `models/coke_can/` (در صورت عدم نیاز).

### ۲.۵. ناقص بودن قابلیت دوربین (`use_camera`)
- **محل باگ:**
  - `nova_gazebo/launch/nova.gazebo.launch.py` (خطوط ۱۴۵–۱۵۰، ۲۹۴–۳۲۱)
  - `nova_gazebo/config/ros_gz_camera_bridge.yaml`
  - `nova_description/urdf/mech/nova.urdf.xacro` (خط ۱۰) و پوشه خالی `urdf/sensors/`
- **شرح باگ:** آرگومان `use_camera` در لانچ فایل‌ها و xacro تعریف و ارسال می‌شود و در صورت `use_camera:=true` نودهای `ros_gz_bridge` و `image_bridge` اجرا می‌شوند؛ اما **هیچ سنسور یا لینک دوربینی در URDF و Gazebo وجود ندارد** و پوشه `urdf/sensors/` خالی است.
- **راه‌حل:**
  - [ ] پیاده‌سازی ماکروی دوربین RGB-D در `urdf/sensors/` و اتصال آن به `nova.urdf.xacro` تحت شرط `use_camera` (یا مستندسازی موقت و غیرفعال‌سازی پل دوربین تا زمان افزودن سنسور).

### ۲.۶. عدم ارسال `controllers_file` در `nova.gazebo.launch.py` و ناسازگاری Multi-Robot / Namespace
- **محل باگ:**
  - `nova_gazebo/launch/nova.gazebo.launch.py` (خطوط ۲۴۱–۲۴۹)
  - `nova_description/urdf/control/gazebo_sim_ros2_control.urdf.xacro` (خطوط ۳، ۹)
  - `nova_moveit_config/launch/load_ros2_controllers.launch.py` (خطوط ۵۴، ۶۷)
- **شرح باگ:**
  1. `nova.gazebo.launch.py` آرگومان `controllers_file` را دریافت و به `robot_state_publisher.launch.py` ارسال نمی‌کند.
  2. ماکروی `load_gazebo_sim_ros2_control_plugin` پارامتر `robot_name` را دریافت می‌کند اما از آن استفاده نمی‌کند و در خط ۹ مسیر `/controller_manager/robot_description:=/robot_description` را به صورت Hardcode ریمپ می‌کند.
  3. در `load_ros2_controllers.launch.py` نیز `--controller-manager /controller_manager` به صورت ثابت (بدون توجه به namespace/robot_name) نوشته شده است.
  4. در `nova.gazebo.launch.py` خط ۲۲۸، لاگ `warn_no_rsp_cmd` بدون بررسی `load_controllers` چاپ می‌شود.
- **راه‌حل:**
  - [ ] افزودن `controllers_file` به `nova.gazebo.launch.py` و استفاده صحیح از namespace در پلاگین `gz_ros2_control` و spawnerها در صورت نیاز به چند ربات.

---

## ۳. باگ‌ها و نواقص `nova_description` (URDF، RViz و Launch)

### ۳.۱. فایل تنظیمات RViz متعلق به ربات دیگری است
- **محل باگ:** `nova_description/rviz/nova_description.rviz` (خطوط ۵۵–۲۰۳)
- **شرح باگ:** درخت لینک‌ها و TF در فایل RViz شامل `base_link`، `link1`..`link6`، `link6_flange` و `gripper_base` / `gripper_left1..3` / `gripper_right1..3` (احتمالاً از ربات دیگری مثل MyCobot) است و هیچ‌کدام از لینک‌های واقعی Nova (`nova_base_link`، `nova_base`، `nova_link1`..`nova_link6`، `nova_end_link`) در آن تعریف نشده‌اند.
- **راه‌حل:**
  - [ ] به‌روزرسانی `nova_description.rviz` بر اساس نام لینک‌های واقعی ربات Nova.

### ۳.۲. تگ اشتباه `<axis>` روی مفصل fixed و متغیرها/فایل‌های بلااستفاده
- **محل باگ:**
  - `nova_description/urdf/mech/nova.urdf.xacro` (خطوط ۸، ۴۲، ۲۵۷–۲۶۲)
  - `nova_description/urdf/mech/macros.xacro` (خط ۲)
  - `nova_description/urdf/control/nova_ros2_control.urdf.xacro` (خط ۱۴)
  - `nova_description/meshes/visual/nova/nova_end_link.STL`
  - پوشه‌های خالی با نام‌های قدیمی: `nova_description/include/manipulator_description` و `nova/include/my_robot`
  - `nova/package.xml` (خط ۶: ذکر `Elfin manipulator`)
- **شرح باگ:**
  - مفصل `fixed` انتهایی (`${prefix}end_joint`) دارای `<axis xyz="0 0 0" />` است که در URDF برای مفصل `fixed` نامعتبر/بی‌معنی است.
  - پارامترهای `base_type` و `density` در `nova.urdf.xacro` و `flange_link` در `nova_ros2_control` تعریف شده‌اند ولی هیچ کاربردی ندارند.
  - فایل `nova_end_link.STL` (هم‌حجم با `nova_link6.STL`) در پوشه مش‌ها هست اما لینک `nova_end_link` بدون هیچ مشی است.
  - نام ربات `my_robot` در `macros.xacro` و نام پوشه‌های `manipulator_description` و `my_robot` و توضیحات `Elfin manipulator` از قالب‌های قبلی باقی مانده‌اند.
- **راه‌حل:**
  - [ ] حذف `<axis xyz="0 0 0" />` از مفصل `fixed`، حذف یا پیاده‌سازی پارامترهای بلااستفاده و پاک‌سازی نام‌های قدیمی باقی‌مانده.

---

## ۴. باگ‌ها و نواقص کنترلرها و MoveIt (`nova_moveit_config`)

### ۴.۱. نبود فایل‌های پیکربندی MoveIt 2 در پکیج `nova_moveit_config`
- **محل باگ:** `nova_moveit_config/`
- **شرح باگ:** این پکیج در حال حاضر فقط `ros2_controllers_template.yaml` و `load_ros2_controllers.launch.py` را دارد و فاقد فایل‌های اصلی MoveIt 2 (`nova.srdf`، `kinematics.yaml`، `joint_limits.yaml`، `moveit_controllers.yaml`، `ompl_planning.yaml` و `move_group.launch.py`) است؛ بنابراین برنامه‌ریزی حرکت MoveIt قابل اجرا نیست.
- **راه‌حل:**
  - [ ] تولید و تکمیل فایل‌های پیکربندی و لانچ MoveIt 2 برای ربات 6-DOF Nova.

### ۴.۲. تنظیمات ناقص `ros2_control` و هشدارهای زمان اجرا در Gazebo
- **محل باگ:**
  - `nova_description/urdf/control/nova_ros2_control.urdf.xacro`
  - `nova_moveit_config/config/nova/ros2_controllers_template.yaml`
  - لاگ اجرا (`console.log` خطوط ۱۱۸–۱۱۹)
- **شرح باگ:**
  1. پیام `[controller_manager]: Enforcing command limits is disabled. Command limits from URDF will be ignored` ثبت می‌شود.
  2. پیام `[gz_ros_control]: The position_proportional_gain has been set to: 0.1` نشان می‌دهد بهره تناسبی پیش‌فرض بسیار کوچک (`0.1`) برای کنترل موقعیت با اینرسی و میرایی (`damping=1.5`, `friction=0.3`) و گرانش استفاده می‌شود که می‌تواند باعث خطای ماندگار یا افتادگی بازو شود.
  3. تنها `state_interface` تعریف‌شده `position` است و `velocity` تعریف نشده است.
  4. در `arm_controller` تنظیمات `constraints` و نرخ انتشار تعریف نشده و `load_ros2_controllers.launch.py` به صورت مستقل فایل کنترلرها را از قالب نمی‌سازد (وابسته به اجرای قبلی `robot_state_publisher.launch.py` است).
  5. در `nova_moveit_config/package.xml` وابستگی `<exec_depend>nova_description</exec_depend>` وجود ندارد.
- **راه‌حل:**
  - [ ] افزودن `velocity` state interface، بررسی و تنظیم پارامترهای کنترلر و بهره کنترلی در `gz_ros2_control`، افزودن `constraints` به `arm_controller` و اصلاح وابستگی‌های `package.xml`.

---

## ۵. پکیج‌های خالی و خطاهای تست و Lint (`colcon test`)

### ۵.۱. پکیج‌های پیاده‌سازی‌نشده (`nova_bringup` و `nova_system_tests`)
- **محل باگ:** `nova_bringup/` و `nova_system_tests/`
- **شرح باگ:** هر دو پکیج فقط اسکلت اولیه (`CMakeLists.txt`، `package.xml`، `LICENSE`) هستند و هیچ کد، لانچ فایل یا تست سیستمی در آن‌ها وجود ندارد.
- **راه‌حل:**
  - [ ] ایجاد لانچ‌های یکپارچه (`bringup`) در `nova_bringup` و تست‌های خودکار در `nova_system_tests`.

### ۵.۲. شکست ۳۲۰ از ۳۴۰ تست در `colcon test` (خطاهای `flake8`، `pep257` و `lint_cmake`)
- **محل باگ:**
  - `nova_description`: ۱۲۸ خطای `flake8`، ۸ خطای `pep257`
  - `nova_gazebo`: ۱۴۴ خطای `flake8`، ۳ خطای `pep257`، ۱ خطای `lint_cmake` (`CMakeLists.txt:12` فاصله اضافی در `install (`)
  - `nova_moveit_config`: ۲۳ خطای `flake8`، ۴ خطای `pep257`، ۱ خطای `lint_cmake` (`CMakeLists.txt:14` فاصله اضافی در `install (`)
- **شرح باگ:** اجرای `colcon test` با کد خطای ۱ شکست می‌خورد (اکثراً به دلیل استفاده از double-quote به جای single-quote، طول خط بیش از ۹۹ کاراکتر و قالب docstring پکیج‌های ament_python/flake8/pep257 و فاصله اضافی `install (` در CMake).
- **راه‌حل:**
  - [ ] رفع فاصله اضافی `install(` در `CMakeLists.txt` پکیج‌های `nova_gazebo` و `nova_moveit_config`.
  - [ ] فرمت و اصلاح فایل‌های پایتون لانچ مطابق `ament_flake8` و `ament_pep257` (یا تنظیم `.flake8` / `setup.cfg` در صورت استفاده عمدی از Black/double-quotes) تا `colcon test` سبز شود.

### ۵.۳. تداخل مسیر فایل موقت و وجود `__pycache__` در `src/`
- **محل باگ:**
  - `nova_description/launch/robot_state_publisher.launch.py` (خطوط ۶۲–۶۶)
  - پوشه‌های `launch/__pycache__/` داخل `nova_description`، `nova_gazebo` و `nova_moveit_config`
- **شرح باگ:** نوشتن فایل موقت کنترلر در مسیر ثابت `/tmp/nova_ros2_control/{robot_name}_ros2_controllers.yaml` بدون شناسه یکتا (مثل PID یا `NamedTemporaryFile`) می‌تواند در اجراهای همزمان تداخل ایجاد کند.
- **راه‌حل:**
  - [ ] استفاده از فایل/دایرکتوری موقت یکتا (یا مدیریت متمرکز و پاک‌سازی ایمن) و حذف `__pycache__`های اضافی در `src/`.

---

## ۶. کارهای معماری و نگهداری قبلی (از TODO قبلی)

### بازساختاری launch فایل‌های `nova_description` و جداسازی مسئولیت‌ها

مسیر فایل فعلی: `nova_description/launch/robot_state_publisher.launch.py`

- [ ] **تمیزسازی `robot_state_publisher.launch.py`**
  - [ ] فقط مسئول پردازش `nova.urdf.xacro` و اجرای نود `robot_state_publisher` باشد (پیش‌فرض `use_rviz` و `use_jsp` روی `false` باشد یا به `display.launch.py` منتقل شوند).
  - [ ] حذف یا انتقال تابع `process_ros2_controllers_config` از `nova_description` و حذف وابستگی `nova_moveit_config` از `nova_description/package.xml` (رفع وابستگی چرخشی/معکوس).
  - [ ] به‌روزرسانی docstring فایل متناسب با وظیفه واقعی آن.

- [ ] **ایجاد فایل `display.launch.py` (یا `view_robot.launch.py`) در `nova_description/launch/`**
  - [ ] برای نمایش و بررسی مدل URDF در RViz، فایل `robot_state_publisher.launch.py` را include کند.
  - [ ] اجرای `joint_state_publisher` / `joint_state_publisher_gui` (`use_jsp` و `jsp_gui` با پیش‌فرض `true`) و `rviz2` (`use_rviz` با پیش‌فرض `true`) را در این فایل قرار دهید.

- [ ] **انتقال تولید `ros2_controllers.yaml` به جای مناسب**
  - [ ] انتقال `process_ros2_controllers_config` (تبدیل `ros2_controllers_template.yaml` به `ros2_controllers.yaml`) به `nova_moveit_config` یا `nova_bringup` تا لانچ‌های کنترلر و MoveIt هم به صورت مستقل کار کنند.

- [ ] **بررسی ارجاعات و بیلد مجدد پس از اصلاحات**

<div dir="ltr">

```bash
colcon build --packages-select nova_description nova_gazebo nova_moveit_config
```

</div>

---

### پاک‌سازی فایل‌های قدیمی ROS 1 / Elfin در `nova_description` (تکمیل‌شده)

- [x] **حذف `include`های قدیمی از `nova.urdf.xacro`** (`nova_robot.gazebo` و `nova_transmission.xacro`)
- [x] **تعیین تکلیف فایل‌های قدیمی در `urdf/mech/`**
- [x] **تست خروجی URDF نهایی**

</div>
