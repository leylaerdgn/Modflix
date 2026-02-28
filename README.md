# Modflix - Duygu ve Anlamsal Benzerlik Tabanlı Film Öneri Sistemi

Modflix, iki farklı öneri yaklaşımını birleştiren yapay zeka destekli bir film öneri uygulamasıdır. Sistem hem duygu seçimine dayalı tür filtreleme hem de kullanıcının yazdığı metni anlamsal olarak analiz eden embedding tabanlı öneri mekanizması içerir.

Sistem Mimarisi: İki Katmanlı Öneri Yapısı

**1) Duygu Seç (Genre Tabanlı Filtreleme)**

Duyguyu ilgili film türleriyle eşleştirir. Yazılan ek kriterleri analiz ederek TMDB filtrelerine dönüştürür. Belirtilen şartlara uygun filmleri listeler.
Çalışma Prensibi:
Kullanıcı bir duygu seçer (örneğin: mutlu, üzgün, stresli...).
Her duygu kutucuğunda akıllı filtreleme olduğu için kullanıcı filtrelemeler yapabilir. Modflix'te mevcut filtreler: 
- Tür (Genre) eşlemesi
- Minimum puan (IMDb)
- Popülerlik / yüksek puan sıralaması
- Yıl, dönem veya dekad filtreleme
- Oy sayısı eşiği
- Ülke seçimi
- Platform filtresi (Netflix, Prime vb.)
- Film süresi (kısa / uzun)

Hızlı ve basit öneri üretir.
Bu katman daha çok kural tabanlı (rule-based) çalışır.

**2) Yaşadıklarını Anlat (Anlamsal Benzerlik – AI Katmanı)**

Kullanıcı yaşadığı bir durumu veya duygusal deneyimini metin olarak yazar. Sistem yaşadığına dair benzer konulu filmler önerir.
Çalışma Prensibi:
- Metni embedding’e (vektöre) dönüştürür.
- Film veri setindeki embedding’lerle karşılaştırır.
- Cosine similarity ile en benzer filmleri sıralar.
- Kullanıcının yaşadığına benzer film önerileri sunar.
Bu yöntem metnin anlamını analiz ederek daha derin ve bağlamsal öneriler üretir.

**⚙️ Kullanılan Teknolojiler
🔹 Backend
- Flask
- Flask-Login
- Flask-SQLAlchemy
- TMDB API entegrasyonu

**🔹 Yapay Zeka & NLP**
- Sentence Transformers (MiniLM multilingual model)
- NumPy ile vektör işlemleri
- Cosine similarity
- Embedding veri seti (.npy)

**🔹 Öneri Yaklaşımları**
- Genre tabanlı filtreleme
- Embedding tabanlı anlamsal arama
- Hibrit filtreleme mantığı

**🔹Geliştirilebilir Alanlar**

Modflix projesi aktif olarak geliştirilebilir bir mimariye sahiptir. İleride eklenebilecek iyileştirmeler:
1. Gerçek Diyalog Yönetimi
- Çok turlu konuşma desteği
- Kullanıcı bağlamını hafızada tutma
- Gerçek bir AI sohbet akışı oluşturma

2. Yaşadıklarını Anlat Modülünün Geliştirilmesi
- Metni daha derin anlama ve duygu analizini güçlendirme
- Daha kişiselleştirilmiş ve bağlamsal öneriler üretme
- Daha hızlı ve ölçeklenebilir arama altyapısı oluşturma
