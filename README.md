# 🏭 Kurumsal Perakende & Tedarik Zinciri Karar Destek Sistemi (DSS)

Bu proje; perakende ve tekstil tedarik zinciri operasyonlarında karşılaşılan manuel Excel süreçlerini ortadan kaldırmak, karar alma mekanizmalarını hızlandırmak ve operasyonel verimliliği artırmak amacıyla geliştirilmiş uçtan uca bir **Karar Destek Sistemi (Decision Support System)** prototipidir.

## 🚀 Projenin Çözdüğü Temel Problem (Acı Noktaları)
Perakende sektöründe tedarik zinciri süreçleri; Ürün Ağacı (BOM) yönetimi, fason atölye takipleri, kalite kontrol (QM) süreçleri ve PLM/ASAS sistemlerindeki tarih takipleri nedeniyle yoğun manuel efor gerektirir. Bu sistem, bu karmaşık süreçleri tek bir çatı altında toplayarak otomatikleştirir.

## 🛠️ Temel Modüller ve Özellikler

1. **Akıllı Ürün Ağacı (BOM) & Malzeme Eşleme Kokpiti (ME2K Simülasyonu):**
   * Üst model (Parent SKU) ile hammadde/aksesuar bileşenlerinin eşleştirilmesi.
   * Eksik parça ve stok maliyeti analizleri.
2. **Fason Üretim & Kalite Muayene (Inspection Lot) Takibi:**
   * Dış fason üreticilere verilen siparişlerin Master Order dönüşüm takibi.
   * Kalite kontrol onay süreçlerinin merkezi yönetimi.
3. **PLM & ASAS Sevkıyat / Ex-Factory & Retail Tarih Takip Kokpiti:**
   * Fabrika çıkış (`Ex-Factory`) ve mağaza varış (`Retail`) tarihlerinin takibi.
   * Gecikme riski taşıyan siparişlerin otomatik erken uyarı mekanizması.
4. **Tedarikçi Maliyet, Ciro ve Ağırlıklı Ortalama Marj Analizi:**
   * Üretici bazlı toplam sipariş ciroları, atölye maliyetleri ve ağırlıklı ortalama kâr marjlarının anlık hesaplanması.
5. **Otomatik Haftalık Yönetici Özet Raporu (Executive Summary):**
   * Üst yönetime sunulacak operasyonel özet raporların ve acil risk listelerinin tek tuşla metin ve TXT olarak dışarı aktarılması.

## 💻 Kullanılan Teknolojiler
* **Python** (Pandas, NumPy)
* **Streamlit** (İnteraktif Web Arayüzü)
* **Plotly** (Gelişmiş Veri Görselleştirme ve Grafikleştirme)
* **SQLite** (İlişkisel Veritabanı ve Migrasyon Yönetimi)

## ⚙️ Kurulum ve Çalıştırma

Projeyi yerel bilgisayarınızda çalıştırmak için aşağıdaki adımları takip edebilirsiniz:

1. Depoyu klonlayın:
   ```bash
   git clone [https://github.com/melisaabulbl/mrp-decision-support-system.git](https://github.com/melisaabulbl/mrp-decision-support-system.git)
   cd mrp-decision-support-system
