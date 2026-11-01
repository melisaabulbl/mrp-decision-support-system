import io
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Kurumsal Perakende & Tedarik Zinciri Karar Destek Sistemi",
    page_icon="🏭",
    layout="wide",
)

st.title("🏭 Kurumsal Perakende & Tedarik Zinciri Karar Destek Sistemi")
st.markdown(
    "Uçtan Uca MRP, Hiyerarşik BOM Patlatma, Fason Yönetimi, Ex-Factory/Retail"
    " Takip ve Otomatik Yönetici Özet Raporlama Kokpiti."
)


# --- VERİTABANI BAŞLANGICI VE OTOMATİK MİGRASYON ---
def init_db():
  with sqlite3.connect("enterprise_retail_mrp.db") as conn:
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT UNIQUE,
                product_name TEXT,
                unit TEXT
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                product_id INTEGER PRIMARY KEY,
                current_stock REAL,
                safety_stock REAL,
                FOREIGN KEY(product_id) REFERENCES products(product_id)
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                product_id INTEGER PRIMARY KEY,
                supplier_name TEXT,
                lead_time_days INTEGER,
                unit_cost REAL,
                reliability_score REAL,
                FOREIGN KEY(product_id) REFERENCES products(product_id)
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS bill_of_materials (
                bom_id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_sku TEXT,
                component_name TEXT,
                quantity_needed REAL,
                component_stock REAL,
                unit_cost REAL DEFAULT 150.0
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS fason_orders (
                fason_id INTEGER PRIMARY KEY AUTOINCREMENT,
                master_order_no TEXT UNIQUE,
                parent_sku TEXT,
                subcontractor_name TEXT,
                order_qty REAL,
                status TEXT,
                inspection_date TEXT
            )
        """)
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS shipment_tracking (
                shipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT UNIQUE,
                ex_factory_date TEXT,
                retail_target_date TEXT,
                cps_status TEXT,
                plm_sync_status TEXT
            )
        """)

    cursor.execute("PRAGMA table_info(suppliers)")
    supplier_columns = [col[1] for col in cursor.fetchall()]
    if "unit_cost" not in supplier_columns:
      cursor.execute("ALTER TABLE suppliers ADD COLUMN unit_cost REAL")
    if "reliability_score" not in supplier_columns:
      cursor.execute("ALTER TABLE suppliers ADD COLUMN reliability_score REAL")

    cursor.execute("PRAGMA table_info(bill_of_materials)")
    bom_columns = [col[1] for col in cursor.fetchall()]
    if "unit_cost" not in bom_columns:
      cursor.execute("ALTER TABLE bill_of_materials ADD COLUMN unit_cost REAL DEFAULT 150.0")

    conn.commit()


init_db()

# --- YAN MENÜ: SİMÜLASYON VE VERİ YÜKLEME ---
with st.sidebar:
  st.header("⚙️ Operasyonel Parametreler")

  daily_demand = st.slider(
      "Günlük Mağaza Satış / Talep Hızı",
      min_value=1,
      max_value=50,
      value=10,
      step=1,
  )

  st.markdown("---")
  st.subheader("📥 Kaggle / Supply Chain Veri Seti Yükleyici")

  uploaded_file = st.file_uploader("Supply Chain CSV Dosyası", type=["csv"])

  if uploaded_file is not None:
    try:
      df_upload = pd.read_csv(uploaded_file)
      columns = df_upload.columns.tolist()

      st.markdown("### 🧩 Sütun Eşleme")

      col_sku = st.selectbox(
          "SKU / Ürün Kodu Sütunu:",
          columns,
          index=columns.index("SKU") if "SKU" in columns else 0,
      )
      col_name = st.selectbox(
          "Ürün Türü / Adı Sütunu:",
          columns,
          index=columns.index("Product type")
          if "Product type" in columns
          else 0,
      )
      col_stock = st.selectbox(
          "Stok Seviyeleri Sütunu:",
          columns,
          index=columns.index("Stock levels")
          if "Stock levels" in columns
          else 0,
      )
      col_lead = st.selectbox(
          "Tedarik/Teslim Süresi Sütunu:",
          columns,
          index=columns.index("Lead times") if "Lead times" in columns else 0,
      )
      col_supplier = st.selectbox(
          "Tedarikçi Adı Sütunu:",
          columns,
          index=columns.index("Supplier name")
          if "Supplier name" in columns
          else 0,
      )

      if st.button("🔄 Verileri Aktar ve Optimizasyonu Başlat"):
        with sqlite3.connect("enterprise_retail_mrp.db") as conn:
          cursor = conn.cursor()
          cursor.execute("DELETE FROM suppliers")
          cursor.execute("DELETE FROM inventory")
          cursor.execute("DELETE FROM products")
          cursor.execute("DELETE FROM bill_of_materials")
          cursor.execute("DELETE FROM fason_orders")
          cursor.execute("DELETE FROM shipment_tracking")

          import random
          from datetime import datetime, timedelta

          random.seed(42)

          for _, row in df_upload.iterrows():
            sku = str(row[col_sku])
            p_name = str(row[col_name]) if pd.notnull(row[col_name]) else "Ürün"
            stock = float(row[col_stock]) if pd.notnull(row[col_stock]) else 0.0
            lead_time = (
                int(row[col_lead]) if pd.notnull(row[col_lead]) else 7
            )
            sup_name = (
                str(row[col_supplier])
                if pd.notnull(row[col_supplier])
                else "Tedarikçi"
            )

            unit_cost = round(random.uniform(50.0, 750.0), 2)
            reliability_score = round(random.uniform(80.0, 99.5), 1)

            cursor.execute(
                "INSERT INTO products (product_code, product_name, unit) "
                "VALUES (?, ?, ?)",
                (sku, f"{p_name} ({sku})", "Adet"),
            )
            p_id = cursor.lastrowid

            cursor.execute(
                "INSERT INTO inventory (product_id, current_stock,"
                " safety_stock) VALUES (?, ?, ?)",
                (p_id, stock, stock * 0.2),
            )

            cursor.execute(
                "INSERT INTO suppliers (product_id, supplier_name,"
                " lead_time_days, unit_cost, reliability_score) VALUES (?, ?,"
                " ?, ?, ?)",
                (p_id, sup_name, lead_time, unit_cost, reliability_score),
            )

            ex_date = (datetime.now() + timedelta(days=random.randint(2, 20))).strftime("%Y-%m-%d")
            re_date = (datetime.now() + timedelta(days=random.randint(25, 45))).strftime("%Y-%m-%d")
            cursor.execute("""
                INSERT OR REPLACE INTO shipment_tracking 
                (product_code, ex_factory_date, retail_target_date, cps_status, plm_sync_status)
                VALUES (?, ?, ?, ?, ?)
            """, (sku, ex_date, re_date, "Sistem Onaylandı", "PLM Aktif (24s Güncel)"))

            p_lower = p_name.lower()
            if (
                "shoe" in p_lower
                or "footwear" in p_lower
                or "ayakkabı" in p_lower
            ):
              components = [
                  (sku, "Deri / Tekstil Saya (Upper)", 1.0, 450.0, 120.0),
                  (sku, "Poliüretan / Eva Taban (Sole)", 1.0, 300.0, 95.0),
                  (sku, "İç Astar ve Tabanlık", 1.0, 800.0, 45.0),
                  (sku, "Özel Tasarım Bağcık", 2.0, 1500.0, 15.0),
              ]
            elif (
                "cosmetic" in p_lower
                or "skincare" in p_lower
                or "krem" in p_lower
            ):
              components = [
                  (sku, "Aktif Kozmetik Formül / Likit", 1.0, 1200.0, 210.0),
                  (sku, "Özel Tasarım Plastik Şişe / Kavanoz", 1.0, 2500.0, 85.0),
                  (sku, "Pompalı Kapak Mekanizması", 1.0, 2000.0, 40.0),
                  (sku, "Markalı Dış Karton Kutu & Etiket", 1.0, 3000.0, 25.0),
              ]
            elif (
                "apparel" in p_lower
                or "clothing" in p_lower
                or "giyim" in p_lower
            ):
              components = [
                  (sku, "Ana Dokuma Kumaş (Metre)", 1.5, 900.0, 180.0),
                  (sku, "Dikiş İpliği ve Tela", 1.0, 4000.0, 30.0),
                  (sku, "Metal Fermuar / Düğme Seti", 2.0, 1500.0, 50.0),
                  (sku, "Barkodlu Kart Etiket", 1.0, 2500.0, 10.0),
              ]
            else:
              components = [
                  (sku, f"Ana Gövde Parçası ({p_name})", 1.0, 600.0, 150.0),
                  (sku, "Montaj Bağlantı Elemanı", 2.0, 1200.0, 20.0),
                  (sku, "Koruyucu Ambalaj Malzemesi", 1.0, 2000.0, 35.0),
              ]

            cursor.executemany(
                "INSERT INTO bill_of_materials (parent_sku, component_name,"
                " quantity_needed, component_stock, unit_cost) VALUES (?, ?, ?, ?, ?)",
                components,
            )

          conn.commit()
        st.success(
            "✅ Veriler yüklendi, PLM/ASAS tarihleri senkronize edildi ve"
            " optimizasyon başlatıldı!"
        )
        st.rerun()

    except Exception as e:
      st.error(f"Veri yükleme hatası: {e}")


# Veritabanından Verileri Çeken Fonksiyon
def get_mrp_data():
  with sqlite3.connect("enterprise_retail_mrp.db") as conn:
    cursor = conn.cursor()
    query = """
        SELECT 
            p.product_code,
            p.product_name,
            COALESCE(i.current_stock, 0) as current_stock,
            COALESCE(s.supplier_name, 'Tedarikçi') as supplier_name,
            COALESCE(s.lead_time_days, 0) as lead_time_days,
            COALESCE(s.unit_cost, 0) as unit_cost,
            COALESCE(s.reliability_score, 0) as reliability_score,
            COALESCE(st.ex_factory_date, 'Belirsiz') as ex_factory,
            COALESCE(st.retail_target_date, 'Belirsiz') as retail_date,
            COALESCE(st.cps_status, 'Normal') as cps_status
        FROM products p
        LEFT JOIN inventory i ON p.product_id = i.product_id
        LEFT JOIN suppliers s ON p.product_id = s.product_id
        LEFT JOIN shipment_tracking st ON p.product_code = st.product_code;
        """
    cursor.execute(query)
    return cursor.fetchall()


rows = get_mrp_data()

# Üst Yönetici Metrikleri
total_skus = len(rows)
risk_count = 0

for r in rows:
  _, _, stock, _, lead_time, _, _, _, _, _ = r
  run_out = stock / daily_demand if daily_demand > 0 else 999
  if run_out <= lead_time:
    risk_count += 1

with sqlite3.connect("enterprise_retail_mrp.db") as conn:
  cursor = conn.cursor()
  cursor.execute("SELECT SUM(quantity_needed * unit_cost) FROM bill_of_materials")
  total_bom_exposure = cursor.fetchone()[0] or 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Toplam İncelenen SKU", total_skus)
col2.metric(
    "🚨 Kritik Riskli SKU",
    risk_count,
    delta="Acil Sipariş",
    delta_color="inverse",
)
col3.metric("Simüle Talep Hızı", f"{daily_demand} Adet/Gün")
col4.metric("💰 Toplam BOM Finansal Risk", f"${total_bom_exposure:,.2f}")

st.markdown("---")

# --- YENİ EKLENEN ÖZELLİK: OTOMATİK HAFTALIK YÖNETİCİ ÖZET RAPORU (EXECUTIVE SUMMARY) ---
st.subheader("📋 Otomatik Haftalık Yönetici Özet Raporu (Executive Summary)")
st.markdown(
    "Planlama uzmanının yöneticisine sunduğu haftalık konsolide operasyon özetini "
    "tek tuşla metin raporu olarak görüntüleyin ve kopyalayın."
)

if total_skus > 0:
  executive_summary_text = f"""
  --- HAFTALIK TEDARİK ZİNCİRİ VE OPERASYON ÖZET RAPORU ---
  • Toplam İncelenen SKU Sayısı: {total_skus}
  • Kritik Risk Altındaki / Acil Sipariş Bekleyen SKU: {risk_count}
  • Günlük Simüle Mağaza Talep Hızı: {daily_demand} Adet/Gün
  • Toplam Ürün Ağacı (BOM) Finansal Risk Maliyeti: ${total_bom_exposure:,.2f}
  
  YÖNETİCİ NOTU: 
  Sistem genelinde kritik eşikteki ürünler için fason atölyeleri ve tedarikçi firmalar ile 
  görüşmeler sağlanmış olup, PLM/ASAS sevkıyat takipleri güncel olarak izlenmektedir.
  ------------------------------------------------------------
  """
  st.text_area("Yöneticiye Sunulacak Özet Rapor Metni:", value=executive_summary_text.strip(), height=180)
  
  st.download_button(
      label="📥 Haftalık Yönetici Özet Raporunu İndir (TXT)",
      data=executive_summary_text.strip(),
      file_name="Haftalik_Yonetici_Ozet_Raporu.txt",
      mime="text/plain",
  )
else:
  st.info("Yönetici özet raporunu oluşturmak için lütfen sol menüden veri seti yükleyin.")

st.markdown("---")

# --- TEDARİKÇİ CİRO & AĞIRLIKLI ORTALAMA MARJ KOKPİTİ ---
st.subheader("📊 Tedarikçi Bazlı Sipariş Ciro & Ağırlıklı Ortalama Marj Kokpiti")

demo_pivot_data = [
    {"ÜRETİCİ": "Tedarikçi Alpha", "MODEL ADI": "MODEL-A1", "ADET": 7568, "ATÖLYE FİYATI": 221.0, "SATIS FİYATI": 243.0},
    {"ÜRETİCİ": "Tedarikçi Alpha", "MODEL ADI": "MODEL-A2", "ADET": 9872, "ATÖLYE FİYATI": 221.0, "SATIS FİYATI": 243.0},
    {"ÜRETİCİ": "Tedarikçi Beta", "MODEL ADI": "MODEL-B1", "ADET": 11544, "ATÖLYE FİYATI": 241.7, "SATIS FİYATI": 260.0},
    {"ÜRETİCİ": "Tedarikçi Alpha", "MODEL ADI": "MODEL-A3", "ADET": 7602, "ATÖLYE FİYATI": 250.0, "SATIS FİYATI": 275.0},
    {"ÜRETİCİ": "Tedarikçi Gamma", "MODEL ADI": "MODEL-G1", "ADET": 11448, "ATÖLYE FİYATI": 195.0, "SATIS FİYATI": 214.5},
    {"ÜRETİCİ": "Tedarikçi Gamma", "MODEL ADI": "MODEL-G2", "ADET": 10590, "ATÖLYE FİYATI": 195.0, "SATIS FİYATI": 214.5},
]

df_pivot_input = pd.DataFrame(demo_pivot_data)
df_pivot_input["Toplam Maliyet (₺)"] = df_pivot_input["ADET"] * df_pivot_input["ATÖLYE FİYATI"]
df_pivot_input["Toplam Ciro (₺)"] = df_pivot_input["ADET"] * df_pivot_input["SATIS FİYATI"]
df_pivot_input["Toplam Kâr (₺)"] = df_pivot_input["Toplam Ciro (₺)"] - df_pivot_input["Toplam Maliyet (₺)"]

supplier_pivot = df_pivot_input.groupby("ÜRETİCİ").agg({
    "ADET": "sum",
    "Toplam Maliyet (₺)": "sum",
    "Toplam Ciro (₺)": "sum",
    "Toplam Kâr (₺)": "sum"
}).reset_index()

supplier_pivot["Ağırlıklı Ort. Maliyet (₺)"] = (supplier_pivot["Toplam Maliyet (₺)"] / supplier_pivot["ADET"]).round(2)
supplier_pivot["Ağırlıklı Ort. Satış (₺)"] = (supplier_pivot["Toplam Ciro (₺)"] / supplier_pivot["ADET"]).round(2)
supplier_pivot["Ağırlıklı Marj (%)"] = ((supplier_pivot["Toplam Kâr (₺)"] / supplier_pivot["Toplam Ciro (₺)"]) * 100).round(2)

p_col1, p_col2 = st.columns([2, 1])

with p_col1:
  st.markdown("### 🏆 Tedarikçi Bazlı Performans & Ciro Özeti")
  st.dataframe(supplier_pivot, use_container_width=True, hide_index=True)

with p_col2:
  fig_supplier_ciro = px.pie(
      supplier_pivot,
      names="ÜRETİCİ",
      values="Toplam Ciro (₺)",
      title="💰 Tedarikçi Ciro Dağılım Payı",
      hole=0.4
  )
  st.plotly_chart(fig_supplier_ciro, use_container_width=True)

st.markdown("---")

# Veri tablosunu hazırlama
table_data = []
for r in rows:
  code, name, stock, supplier, lead_time, cost, reliability, ex_fac, ret_date, cps_st = r
  run_out_days = stock / daily_demand if daily_demand > 0 else 999.0

  if stock == 0:
    status_short = "Stok Tükendi"
    status_detail = "🚨 Stok Tamamen Tükendi!"
  elif run_out_days <= lead_time:
    status_short = "Kritik Risk"
    status_detail = (
        f"⚠️ Kritik Risk: Stok Ömrü ({round(run_out_days, 1)} Gün) <= Tedarik"
        f" Süresi ({lead_time} Gün)"
    )
  else:
    status_short = "Güvenli Seviye"
    status_detail = "✅ Güvenli Seviye"

  table_data.append({
      "SKU Kodu": code,
      "Ürün / Tip": name,
      "Mevcut Stok": stock,
      "Birim Maliyet ($)": cost,
      "Ex-Factory Tarihi": ex_fac,
      "Retail Hedef Tarihi": ret_date,
      "CPS / ASAS Durum": cps_st,
      "Tedarik Süresi (Gün)": lead_time,
      "Güvenilirlik (%)": reliability,
      "Tedarikçi Firma": supplier,
      "Risk Durumu": status_detail,
      "_status_short": status_short,
  })

df = pd.DataFrame(table_data)

# --- PLOTLY İNTERAKTİF GÖRSELLEŞTİRME PANELİ ---
st.subheader("📈 Operasyonel Görselleştirme Paneli")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
  risk_counts = df["_status_short"].value_counts().reset_index()
  risk_counts.columns = ["Risk Durumu", "Adet"]
  fig_pie = px.pie(
      risk_counts,
      names="Risk Durumu",
      values="Adet",
      title="🎯 SKU Risk Dağılım Oranı",
      hole=0.4,
      color="Risk Durumu",
      color_discrete_map={
          "Kritik Risk": "#ff4d4d",
          "Stok Tükendi": "#800000",
          "Güvenli Seviye": "#2ecc71",
      },
  )
  st.plotly_chart(fig_pie, use_container_width=True)

with chart_col2:
  df_risky_chart = df[df["_status_short"].isin(["Kritik Risk", "Stok Tükendi"])]
  if not df_risky_chart.empty:
    sup_risk = df_risky_chart["Tedarikçi Firma"].value_counts().reset_index()
    sup_risk.columns = ["Tedarikçi Firma", "Riskli SKU Sayısı"]
    fig_bar = px.bar(
        sup_risk,
        x="Tedarikçi Firma",
        y="Riskli SKU Sayısı",
        title="⚠️ Tedarikçi Bazlı Kritik Risk Adetleri",
        color="Riskli SKU Sayısı",
        color_continuous_scale="Reds",
    )
    st.plotly_chart(fig_bar, use_container_width=True)
  else:
    st.info("✨ Mevcut talep hızında riskli tedarikçi bulunmuyor.")

st.markdown("---")

# --- PLM / ASAS SEVKİYAT VE TARİH KONTROL KOKPİTİ ---
st.subheader("📅 PLM & ASAS Sevkıyat / Ex-Factory & Retail Tarih Takip Kokpiti")

plm_col1, plm_col2 = st.columns(2)

with plm_col1:
  st.markdown("### ✍️ SKU Bazlı Tarih & Sevkiyat Güncelleme")
  with sqlite3.connect("enterprise_retail_mrp.db") as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT product_code FROM products")
    skus_for_plm = [row[0] for row in cursor.fetchall()]

  if skus_for_plm:
    p_sku_sel = st.selectbox("Seçilen SKU Kodu", skus_for_plm, key="plm_sku_select")
    new_ex_date = st.date_input("Yeni Ex-Factory (Fabrika Çıkış) Tarihi")
    new_ret_date = st.date_input("Yeni Retail (Mağaza Varış) Tarihi")
    new_cps_status = st.selectbox("CPS / ASAS Durum Güncellemesi", ["Sevk Edildi", "Üretimde Bekliyor", "Gecikmede", "Normal"])

    if st.button("🔄 PLM / ASAS Tablosunu Güncelle", type="primary"):
      try:
        with sqlite3.connect("enterprise_retail_mrp.db") as conn:
          cursor = conn.cursor()
          cursor.execute("""
              INSERT OR REPLACE INTO shipment_tracking 
              (product_code, ex_factory_date, retail_target_date, cps_status, plm_sync_status)
              VALUES (?, ?, ?, ?, ?)
          """, (p_sku_sel, str(new_ex_date), str(new_ret_date), new_cps_status, "Manuel Revize Edildi"))
          conn.commit()
        st.success(f"✅ {p_sku_sel} nolu ürünün sevk tarihleri ve CPS durumu güncellendi!")
        st.rerun()
      except Exception as e:
        st.error(f"Hata: {e}")
  else:
    st.info("Tarih takibi için önce sol menüden veri seti yükleyin.")

with plm_col2:
  st.markdown("### 📊 Otomatik ASAS / PLM Takip Özeti")
  with sqlite3.connect("enterprise_retail_mrp.db") as conn:
    ship_df = pd.read_sql_query("SELECT product_code AS 'SKU', ex_factory_date AS 'Ex-Factory', retail_target_date AS 'Retail Hedef', cps_status AS 'CPS Durum', plm_sync_status AS 'PLM Veri' FROM shipment_tracking", conn)

  if not ship_df.empty:
    st.dataframe(ship_df, use_container_width=True, hide_index=True)
  else:
    st.info("Henüz yüklenmiş sevkiyat takip kaydı bulunmuyor.")

st.markdown("---")

# --- TEDARİKÇİ MALİYET & PERFORMANS OPTİMİZASYON MATRİXİ ---
st.subheader("💡 Tedarikçi Maliyet & Performans Optimizasyon Matrisi")

if not df.empty:
  supplier_summary = (
      df.groupby("Tedarikçi Firma")
      .agg({
          "SKU Kodu": "count",
          "Birim Maliyet ($)": "mean",
          "Tedarik Süresi (Gün)": "mean",
          "Güvenilirlik (%)": "mean",
      })
      .reset_index()
  )

  supplier_summary.columns = [
      "Tedarikçi Firma",
      "Yönetilen SKU Sayısı",
      "Ort. Birim Maliyet ($)",
      "Ort. Teslim Süresi (Gün)",
      "Ort. Güvenilirlik Skoru (%)",
  ]
  supplier_summary["Ort. Birim Maliyet ($)"] = supplier_summary[
      "Ort. Birim Maliyet ($)"
  ].round(2)
  supplier_summary["Ort. Teslim Süresi (Gün)"] = supplier_summary[
      "Ort. Teslim Süresi (Gün)"
  ].round(1)
  supplier_summary["Ort. Güvenilirlik Skoru (%)"] = supplier_summary[
      "Ort. Güvenilirlik Skoru (%)"
  ].round(1)

  best_cost = supplier_summary.loc[
      supplier_summary["Ort. Birim Maliyet ($)"].idxmin()
  ]["Tedarikçi Firma"]
  best_speed = supplier_summary.loc[
      supplier_summary["Ort. Teslim Süresi (Gün)"].idxmin()
  ]["Tedarikçi Firma"]
  best_reliable = supplier_summary.loc[
      supplier_summary["Ort. Güvenilirlik Skoru (%)"].idxmax()
  ]["Tedarikçi Firma"]

  opt_col1, opt_col2 = st.columns([2, 1])

  with opt_col1:
    st.dataframe(
        supplier_summary, use_container_width=True, hide_index=True
    )

  with opt_col2:
    st.markdown("### 🏆 Yapay Zeka Karar Önerisi")
    st.info(f"💰 **En Ekonomik Tedarikçi:** {best_cost}")
    st.success(f"⚡ **En Hızlı / Çevik Tedarikçi:** {best_speed}")
    st.warning(f"🛡️ **En Güvenilir / Kaliteli Tedarikçi:** {best_reliable}")

st.markdown("---")

# --- AKILLİ BOM & ME2K MALZEME EŞLEME KOKPİTİ ---
st.subheader("🛠️ Akıllı Ürün Ağacı (BOM) & Malzeme Eşleme Kokpiti (ME2K Simülasyonu)")

with sqlite3.connect("enterprise_retail_mrp.db") as conn:
  cursor = conn.cursor()
  cursor.execute("SELECT product_code, product_name FROM products")
  model_rows = cursor.fetchall()

if model_rows:
  cockpit_col1, cockpit_col2 = st.columns(2)

  with cockpit_col1:
    selected_target_model = st.selectbox(
        "Hedef Ürün Modeli (Parent SKU)",
        [f"{r[0]} - {r[1]}" for r in model_rows],
        key="smart_bom_target_sku",
    )
    target_sku_code = selected_target_model.split(" - ")[0]

  with cockpit_col2:
    pasted_material_codes = st.text_area(
        "SD Belgesi / Malzeme Bileşenlerini Yapıştırın (Her satıra bir bileşen)",
        placeholder="Örn:\nSezonluk Özel Aksesuar\nDestek Karton",
        key="smart_bom_pasted_area",
    )

  if st.button("🔍 Malzemeleri Doğrula ve BOM Hiyerarşisine Ekle", type="primary"):
    if target_sku_code and pasted_material_codes:
      raw_items = [
          item.strip()
          for item in pasted_material_codes.replace(",", "\n").split("\n")
          if item.strip()
      ]

      with sqlite3.connect("enterprise_retail_mrp.db") as conn:
        cursor = conn.cursor()
        added_count = 0
        for comp_name in raw_items:
          cursor.execute(
              "SELECT COUNT(*) FROM bill_of_materials WHERE parent_sku = ? AND"
              " component_name = ?",
              (target_sku_code, comp_name),
          )
          exists = cursor.fetchone()[0]
          if not exists:
            cursor.execute(
                "INSERT INTO bill_of_materials (parent_sku, component_name,"
                " quantity_needed, component_stock, unit_cost) VALUES (?, ?, ?, ?, ?)",
                (target_sku_code, comp_name, 1.0, 75.0, 150.0),
            )
            added_count += 1
        conn.commit()

      st.success(
          f"✅ Başarılı! {added_count} yeni bileşen '{target_sku_code}' nolu"
          " modelin Ürün Ağacına (BOM) eklendi."
      )
      st.rerun()
    else:
      st.error("Lütfen bir hedef model seçin ve bileşen listesini girin.")
else:
  st.info("Veritabanında ürün bulunmuyor. Önce sol menüden veri seti yükleyin.")

st.markdown("---")

# --- FASON ÜRETİM & KALİTE MUAYENE (QM) KOKPİTİ ---
st.subheader("🏭 Fason Üretim & Kalite Muayene (Inspection Lot) Kokpiti")

fason_col1, fason_col2 = st.columns(2)

with fason_col1:
  st.markdown("### 📝 Yeni Fason Master Order & QM Girişi")
  with sqlite3.connect("enterprise_retail_mrp.db") as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT product_code FROM products")
    skus_for_fason = [row[0] for row in cursor.fetchall()]

  if skus_for_fason:
    f_sku = st.selectbox("Fason Üretilecek SKU", skus_for_fason, key="fason_sku_select")
    f_subcontractor = st.text_input("Fason Üretici / Atölye Adı", value="Örn: Partner Atölye Ltd.")
    f_order_no = st.text_input("Master Order Kodu", value="MO-2026-9901")
    f_qty = st.number_input("Üretim / Sipariş Adedi", min_value=1, value=500)
    f_status = st.selectbox("Süreç Durumu", ["Üretimde", "Kalite Kontrolde (Inspection)", "Onaylandı / Stokta"])
    f_insp_date = st.date_input("Inspection (Muayene) Tarihi")

    if st.button("🚀 Master Order ve Inspection Lot Oluştur", type="primary"):
      try:
        with sqlite3.connect("enterprise_retail_mrp.db") as conn:
          cursor = conn.cursor()
          cursor.execute("""
              INSERT OR REPLACE INTO fason_orders 
              (master_order_no, parent_sku, subcontractor_name, order_qty, status, inspection_date)
              VALUES (?, ?, ?, ?, ?, ?)
          """, (f_order_no, f_sku, f_subcontractor, f_qty, f_status, str(f_insp_date)))
          conn.commit()
        st.success(f"✅ {f_order_no} nolu Master Order başarıyla oluşturuldu ve Inspection Lot bağlandı!")
        st.rerun()
      except Exception as e:
        st.error(f"Hata: {e}")
  else:
    st.info("Fason emirleri açmak için önce sol menüden veri seti yükleyin.")

with fason_col2:
  st.markdown("### 📋 Aktif Fason & Kalite Takip Paneli")
  with sqlite3.connect("enterprise_retail_mrp.db") as conn:
    fason_df = pd.read_sql_query("SELECT master_order_no AS 'Master Order', parent_sku AS 'SKU', subcontractor_name AS 'Fasoncu', order_qty AS 'Adet', status AS 'Durum', inspection_date AS 'Muayene Tarihi' FROM fason_orders", conn)

  if not fason_df.empty:
    st.dataframe(fason_df, use_container_width=True, hide_index=True)
  else:
    st.info("Henüz oluşturulmuş aktif fason master order kaydı bulunmuyor.")

st.markdown("---")

# --- ÇOKLU SEVİYE HİYERARŞİK BOM PATLATMA ---
st.subheader("🌳 Çoklu Seviye Hiyerarşik BOM (Ürün Ağacı) Patlatma Simülasyonu")

with sqlite3.connect("enterprise_retail_mrp.db") as conn:
  cursor = conn.cursor()
  cursor.execute("SELECT product_code FROM products")
  available_skus = [row[0] for row in cursor.fetchall()]

if available_skus:
  bom_col1, bom_col2 = st.columns([1, 2])

  with bom_col1:
    selected_parent = st.selectbox(
        "İncelenecek / Satılacak Ürün SKU:", available_skus
    )
    sold_quantity = st.number_input(
        "Simüle Edilen Satış Adedi:", min_value=1, max_value=1000, value=15
    )

  with bom_col2:
    with sqlite3.connect("enterprise_retail_mrp.db") as conn:
      bom_df = pd.read_sql_query(
          f"SELECT component_name AS 'Alt Bileşen', quantity_needed AS 'Birim"
          f" Başına İhtiyaç', component_stock AS 'Depo Mevcut Stok', unit_cost AS 'Birim Maliyet ($)' FROM"
          f" bill_of_materials WHERE parent_sku = '{selected_parent}'",
          conn,
      )

    if not bom_df.empty:
      bom_df["Toplam Gereksinim"] = (
          bom_df["Birim Başına İhtiyaç"] * sold_quantity
      )
      bom_df["Kalan Net Stok"] = (
          bom_df["Depo Mevcut Stok"] - bom_df["Toplam Gereksinim"]
      )
      bom_df["Bileşen Durumu"] = bom_df["Kalan Net Stok"].apply(
          lambda x: "✅ Yeterli Stok"
          if x >= 0
          else f"🚨 EKSİK ({abs(round(x, 1))}) Adet!"
      )
      bom_df["Toplam Bileşen Maliyeti ($)"] = bom_df["Birim Başına İhtiyaç"] * bom_df["Birim Maliyet ($)"]

      st.markdown(
          f"**{selected_parent}** için Kategoriye Özel Ürün Ağacı (BOM) Patlatma"
          " Sonucu & Maliyet Dağılımı:"
      )
      st.dataframe(bom_df, use_container_width=True, hide_index=True)
else:
  st.warning("Lütfen sol menüden veri setini yeniden yükleyin.")

st.markdown("---")

# --- RAPOR DIŞA AKTARMA (EXECUTIVE EXPORT) BÖLÜMÜ ---
st.subheader("📊 Stok Erime ve Tedarik Gecikme Detay Tablosu")

df_risky = df[df["_status_short"].isin(["Kritik Risk", "Stok Tükendi"])].copy()

export_col1, export_col2 = st.columns([1, 1])

with export_col1:
  csv_all = df.drop(columns=["_status_short"]).to_csv(index=False).encode(
      "utf-8-sig"
  )
  st.download_button(
      label="📥 Tüm Envanter Analiz Raporunu İndir (Excel/CSV)",
      data=csv_all,
      file_name="Tüm_Envanter_MRP_Raporu.csv",
      mime="text/csv",
  )

with export_col2:
  if not df_risky.empty:
    csv_risky = df_risky.drop(columns=["_status_short"]).to_csv(index=False).encode(
        "utf-8-sig"
    )
    st.download_button(
        label="🚨 Acil Sipariş & Kritik Risk Raporunu İndir (Yönetici Özel)",
        data=csv_risky,
        file_name="Kritik_Risk_Acil_Siparis_Listesi.csv",
        mime="text/csv",
    )
  else:
    st.success("✅ Şu an acil sipariş gerektiren kritik riskli ürün yok.")


# SATIR RENKLENDİRME FONKS
