<!DOCTYPE html>
<html lang="am">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>መላ ህብረት ስራ ማህበር (Mela SACCO)</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    :root {
      --bg-color: #0f172a;
      --card-bg: #1e293b;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #3b82f6;
      --accent-gold: #f59e0b;
      --danger: #ef4444;
      --success: #10b981;
      --border-color: #334155;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: var(--bg-color);
      color: var(--text-main);
      margin: 0; padding: 20px;
    }

    .container { width: 100%; max-width: 1400px; margin: 0 auto; }
    
    /* Navigation / Folder Tabs */
    .nav-tabs {
      display: flex; gap: 10px; margin-bottom: 20px; overflow-x: auto; padding-bottom: 5px;
    }
    .tab-btn {
      background: var(--card-bg); border: 1px solid var(--border-color); color: var(--text-muted);
      padding: 12px 20px; border-radius: 10px; cursor: pointer; font-weight: bold; white-space: nowrap; transition: 0.2s;
    }
    .tab-btn.active { background: var(--primary); color: white; border-color: var(--primary); }

    .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }

    .card {
      background: var(--card-bg); border: 1px solid var(--border-color);
      border-radius: 16px; padding: 24px; margin-bottom: 20px;
    }

    .btn {
      background-color: var(--primary); color: white; border: none;
      padding: 12px 18px; border-radius: 10px; font-weight: bold; cursor: pointer; width: 100%; font-size: 14px;
    }
    .btn-success { background-color: var(--success); }
    .btn-warning { background-color: var(--accent-gold); color: #000; }

    .input-group { margin-bottom: 14px; }
    .input-group label { display: block; font-size: 13px; margin-bottom: 6px; color: var(--text-muted); }
    .input-group input, .input-group textarea {
      width: 100%; padding: 11px; border-radius: 8px;
      border: 1px solid var(--border-color); background-color: var(--bg-color); color: var(--text-main); box-sizing: border-box;
    }

    /* Accordion / Folder Section */
    .accordion { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; margin-bottom: 12px; overflow: hidden; }
    .accordion-header { padding: 16px 20px; cursor: pointer; font-weight: bold; display: flex; justify-content: space-between; background: rgba(255,255,255,0.02); }
    .accordion-body { padding: 20px; display: none; border-top: 1px solid var(--border-color); font-size: 14px; color: var(--text-muted); line-height: 1.6; }
    .accordion.open .accordion-body { display: block; }

    .hidden { display: none; }
  </style>
</head>
<body>

<div class="container">

  <!-- Folder Navigation Tabs -->
  <div class="nav-tabs">
    <button class="tab-btn active" onclick="switchTab('about-tab')">🏢 ስለ መላ ሳኮ</button>
    <button class="tab-btn" onclick="switchTab('reg-tab')">📝 የአባልነት ምዝገባ</button>
    <button class="tab-btn" onclick="switchTab('guarantor-tab')">🤝 የዋስትና ሰነድ ማስገቢያ</button>
    <button class="tab-btn hidden" id="admin-tab-btn" onclick="switchTab('admin-tab')">⚙️ አድሚን ፓናል</button>
  </div>

  <!-- TAB 1: ስለ መላ ሳኮ እና ስለ ድርጅቱ (About & Goals Folder) -->
  <div id="about-tab" class="tab-content">
    <div class="card">
      <h2>🏥 እንኳን ወደ መላ ህብረት ስራ ማህበር (Mela SACCO) በደህና መጡ!</h2>
      <p>መላ ሳኮ ለአባላቱ ዘመናዊ፣ አስተማማኝና የተቀላጠፈ የቁጠባ፣ የብድርና የኢንቨስትመንት አገልግሎቶችን የሚያቀርብ ዲጂታል ሲስተም ነው።</p>
    </div>

    <div class="accordion" onclick="toggleAccordion(this)">
      <div class="accordion-header"><span>🎯 የድርጅቱ ዓላማና ግብ (Mission & Vision)</span> <span>▼</span></div>
      <div class="accordion-body">
        <p><b>ዓላማችን፦</b> የአባላቶቻችንን የቁጠባ ባህል ማሳደግ፣ አነስተኛና መካከለኛ ንግዶችን በብድር ማጠናከር እንዲሁም የተቀላጠፈ የዲጂታል ፋይናንስ አገልግሎት ማቅረብ ነው።</p>
        <p><b>ግባችን፦</b> በቴክኖሎጂ የተደገፈ ግልጽ፣ ፈጣን እና ደህንነቱ የተጠበቀ የብድርና ቁጠባ ስርዓት በመዘርጋት የአባላትን ኢኮኖሚያዊ አቅም ማሳደግ ነው።</p>
      </div>
    </div>

    <div class="accordion" onclick="toggleAccordion(this)">
      <div class="accordion-header"><span>📜 የብድር ዓይነቶች (Loan Types)</span> <span>▼</span></div>
      <div class="accordion-body">
        <ul>
          <li><b>የአጭር ጊዜ ብድር፦</b> እስከ 3 ወር የሚቆይ ለአስቸኳይ የካፒታል ፍላጎቶች የሚሆን።</li>
          <li><b>የንግድ ማስፋፊያ ብድር፦</b> እስከ ቁጠባዎ 3 እጥፍ የሚፈቀድና እስከ 12 ወር የሚከፈልበት።</li>
          <li><b>የአስቸኳይ ጊዜ ብድር፦</b> በ12 ሰዓታት ውስጥ የሚፈቀድ አጭር ጊዜ ብድር።</li>
        </ul>
      </div>
    </div>

    <div class="accordion" onclick="toggleAccordion(this)">
      <div class="accordion-header"><span>💰 የቁጠባና የአክሲዮን ስርዓት</span> <span>▼</span></div>
      <div class="accordion-body">
        <p><b>መደበኛ ቁጠባ፦</b> አባላት በየወሩ በቋሚነት የሚያስቀምጡት የቁጠባ መጠን።</p>
        <p><b>የአክሲዮን ድርሻ፦</b> አባላት የድርጅቱ ባለቤት እንዲሆኑ የሚያስችላቸው የአክሲዮን ክፍፍል።</p>
      </div>
    </div>
  </div>

  <!-- TAB 2: የአባልነት ምዝገባ ቅጽ (Member Registration Only) -->
  <div id="reg-tab" class="tab-content hidden">
    <div class="card" style="max-width: 600px; margin: 0 auto;">
      <h3>📝 የአባልነት መመዝገቢያ ቅጽ</h3>
      <p>አባል ለመሆን እባክዎን የሚከተሉትን መረጃዎች በጥንቃቄ ይሙሉ፦</p>
      
      <div class="input-group">
        <label>ሙሉ ስም</label>
        <input type="text" id="reg-name" placeholder="ሙሉ ስም ያስገቡ">
      </div>
      <div class="input-group">
        <label>ስልክ ቁጥር (በ 09 ወይም 07 የሚጀምር)</label>
        <input type="text" id="reg-phone" placeholder="09xxxxxxxx ወይም 07xxxxxxxx">
      </div>
      <div class="input-group">
        <label>TIN ቁጥር</label>
        <input type="text" id="reg-tin" placeholder="የቲን ቁጥር">
      </div>
      <div class="input-group">
        <label>VAT ቁጥር (ካለዎት)</label>
        <input type="text" id="reg-vat" placeholder="የቫት ቁጥር (አማራጭ)">
      </div>
      <div class="input-group">
        <label>የንግድ ፈቃድ (ፎቶ/File Attachment)</label>
        <input type="file" id="reg-license-file" accept="image/*">
      </div>
      <button class="btn btn-success" onclick="submitRegistration()">📩 የአባልነት ማመልከቻ ላክ</button>
    </div>
  </div>

  <!-- TAB 3: የዋስትና ሰነድ ማስገቢያ (Guarantor & Check Section) -->
  <div id="guarantor-tab" class="tab-content hidden">
    <div class="card" style="max-width: 600px; margin: 0 auto;">
      <h3>🤝 የዋስትና እና የቼክ ሰነድ ማስገቢያ</h3>
      <p>አባል ሆነው ከተመዘገቡ በኋላ የተሰጠዎትን <b>የመዝገብ ቁጥር (Member ID)</b> በማስገባት የዋስትና ሰነድዎን ያያይዙ፦</p>
      
      <div class="input-group">
        <label>የአባልነት መዝገብ ቁጥር (Member ID/Telegram ID)</label>
        <input type="text" id="guar-member-id" placeholder="የመዝገብ ቁጥርዎን ያስገቡ">
      </div>
      <div class="input-group">
        <label>የተበዳሪው የቼክ ቁጥር</label>
        <input type="text" id="guar-user-check" placeholder="የእርስዎ ቼክ ቁጥር">
      </div>
      <div class="input-group">
        <label>የዋስ ሙሉ ስም</label>
        <input type="text" id="guar-name" placeholder="የዋስ ስም">
      </div>
      <div class="input-group">
        <label>የዋስ ስልክ ቁጥር (09/07)</label>
        <input type="text" id="guar-phone" placeholder="09xxxxxxxx">
      </div>
      <div class="input-group">
        <label>የዋሱ የቼክ ቁጥር</label>
        <input type="text" id="guar-check" placeholder="የዋሱ ቼክ ቁጥር">
      </div>
      <button class="btn btn-warning" onclick="submitGuarantorDoc()">📩 የዋስትና ሰነድ ላክ</button>
    </div>
  </div>

  <!-- TAB 4: የአድሚን መቆጣጠሪያ ፓናል (Admin Panel) -->
  <div id="admin-tab" class="tab-content hidden">
    <div class="card" style="border: 2px solid var(--accent-gold);">
      <h2>⚙️ የአድሚን መቆጣጠሪያ ፓናል (Admin Dashboard)</h2>
      <p>አድሚን፣ እዚህ ጋር የአባላትን ቁጠባ፣ ብድርና የዋስትና ሰነዶች ማስተዳደር ይችላሉ።</p>
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>💳 ቁጠባና ብድር ማስተካከያ</h3>
        <div class="input-group"><label>የአባሉ የመዝገብ/Telegram ID</label><input type="number" id="adm-target-id" placeholder="Telegram ID"></div>
        <div class="input-group"><label>የሚጨመር ቁጠባ (ETB)</label><input type="number" id="adm-savings" placeholder="0.00"></div>
        <div class="input-group"><label>የተፈቀደ ብድር (ETB)</label><input type="number" id="adm-loan" placeholder="0.00"></div>
        <button class="btn" onclick="updateUserAccount()">✅ መረጃውን አዘምን</button>
      </div>

      <div class="card">
        <h3>📢 ለአባላት ማስታወቂያ መላኪያ</h3>
        <div class="input-group"><label>የማስታወቂያ መልእክት</label><textarea id="adm-broadcast-msg" rows="4" placeholder="ማስታወቂያ ይፃፉ..."></textarea></div>
        <button class="btn" onclick="sendBroadcast()">🚀 ማስታወቂያ ላክ</button>
      </div>
    </div>
  </div>

</div>

<script>
  const tg = window.Telegram.WebApp;
  tg.expand();

  const currentUserId = tg.initDataUnsafe?.user?.id;
  const ADMIN_ID = 5351353727;

  if (currentUserId === ADMIN_ID) {
    document.getElementById('admin-tab-btn').classList.remove('hidden');
  }

  function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById(tabId).classList.remove('hidden');
    event.target.classList.add('active');
  }

  function toggleAccordion(element) {
    element.classList.toggle('open');
  }

  // 09 ወይም 07 የሚጀምር የ10 ዲጂት ስልክ ቁጥር ማረጋገጫ
  function validateEthiopianPhone(phone) {
    const phoneRegex = /^(09|07)\d{8}$/;
    return phoneRegex.test(phone);
  }

  function getBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  }

  async function submitRegistration() {
    const fullName = document.getElementById('reg-name').value;
    const phone = document.getElementById('reg-phone').value;
    const tin = document.getElementById('reg-tin').value;
    const vat = document.getElementById('reg-vat').value;
    const fileInput = document.getElementById('reg-license-file').files[0];

    if (!fullName || !phone || !tin) {
      alert("እባክዎን ስም፣ ስልክ ቁጥር እና ቲን ቁጥር ያስገቡ!");
      return;
    }

    if (!validateEthiopianPhone(phone)) {
      alert("⚠️ እባክዎን ትክክለኛ የኢትዮጵያ ስልክ ቁጥር ያስገቡ! (በ 09 ወይም 07 የሚጀምር 10 ዲጂት ቁጥር)");
      return;
    }

    let fileBase64 = "";
    if (fileInput) fileBase64 = await getBase64(fileInput);

    tg.sendData(JSON.stringify({
      action: "register",
      fullName: fullName,
      phone: phone,
      tin: tin,
      vat: vat,
      licenseImg: fileBase64
    }));
  }

  async function submitGuarantorDoc() {
    const memberId = document.getElementById('guar-member-id').value;
    const userCheck = document.getElementById('guar-user-check').value;
    const gName = document.getElementById('guar-name').value;
    const gPhone = document.getElementById('guar-phone').value;
    const gCheck = document.getElementById('guar-check').value;

    if (!memberId || !userCheck || !gName || !gPhone) {
      alert("እባክዎን ሁሉንም የዋስትና መረጃዎች በጥንቃቄ ይሙሉ!");
      return;
    }

    if (!validateEthiopianPhone(gPhone)) {
      alert("⚠️ እባክዎን ትክክለኛ የዋስ ስልክ ቁጥር ያስገቡ! (በ 09 ወይም 07 የሚጀምር 10 ዲጂት)");
      return;
    }

    tg.sendData(JSON.stringify({
      action: "submit_guarantor",
      memberId: memberId,
      userCheck: userCheck,
      guarantorName: gName,
      guarantorPhone: gPhone,
      guarantorCheck: gCheck
    }));
  }

  function updateUserAccount() {
    const targetUser = document.getElementById('adm-target-id').value;
    const savings = document.getElementById('adm-savings').value || 0;
    const loan = document.getElementById('adm-loan').value || 0;

    if (!targetUser) return alert("የአባሉን ID ያስገቡ!");

    tg.sendData(JSON.stringify({
      action: "update_account", targetUser: targetUser, savings: savings, loan: loan
    }));
  }

  function sendBroadcast() {
    const msg = document.getElementById('adm-broadcast-msg').value;
    if (!msg) return alert("መልእክት ያስገቡ");
    tg.sendData(JSON.stringify({ action: "broadcast", message: msg }));
  }
</script>

</body>
</html>
