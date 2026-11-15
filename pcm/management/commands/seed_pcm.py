"""Isi database kosong dengan data riil PCM Moyudan.

Sumber utama: https://muhammadiyahmoyudan.or.id/pcm/ (susunan pimpinan 2022-2027, program kerja).
Data yang belum diperoleh sengaja dikosongkan / "belum tersedia" -- isi lewat admin atau tambahkan
di daftar RANTING, BERITA, dsb. di bawah setelah data diverifikasi ke pengurus.
Perintah ini idempotent: aman dijalankan berulang kali.
"""
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils import timezone

from pcm.models import AmalUsaha, Berita, Pimpinan, Profil, Ranting, TautanTerkait

HERO_URL = "https://muhammadiyahmoyudan.or.id/wp-content/uploads/2023/10/IMG_7469-1.jpg"

PENASEHAT = ["Drs. H. Abdullah Effendi", "H. Sudiyana Irsyad", "Ngadi Susilo, BA", "Dr. H. Zainudin Akhid"]

INTI = [
    ("Ketua", "H. Abu Hanifah, S.Ag, MSI"),
    ("Wakil Ketua 1 (Koord. Tabligh dan Wakaf)", "Drs. H. Suisdialwan, MA"),
    ("Wakil Ketua 2 (Koord. MPKS dan Ekonomi)", "H. Imam Triyono, S.Ag, M.Si"),
    ("Wakil Ketua 3 (Koord. Dikdasmen PNF dan Kader)", "Drs. H. Sarjono, M.Si"),
    ("Wakil Ketua 4 (Koord. MPKU, Litbang dan TI)", "H. Abu Yazid, SIP, MM"),
    ("Sekretaris", "H. Heru Suprayitno, S.Ag"),
    ("Wakil Sekretaris", "Haris Bahalwan, S.Ag"),
    ("Bendahara", "Drs. H. Suharyanto, MA"),
    ("Wakil Bendahara", "Difa Nuarisapta, S.Pd"),
]

# Ketua, Wakil Ketua, Sekretaris 1, Sekretaris 2 (anggota majelis bisa ditambah lewat admin)
MAJELIS = {
    "Majelis Tabligh": ["H. Yulianto, S.Pd", "Muhammad Zamroni", "Tri Wiyoko S.Pd.I", "Arif Gunawan S.Ag"],
    "Majelis Dikdasmen dan Pendidikan Non-Formal": ["H. Mardi, S.Pd, M.Pd", "Drs. Djemidi", "Joko Suwahyono, S.Pd", "Asfandi, S.Pd, M.Pd"],
    "Majelis Pembinaan Kesehatan Umum": ["drh. H. Haryanto", "H. Ridwanto, SH, M.Hum", "Jazuli, S.Sos", "Agung Rusdiyanto, S.Pd"],
    "Majelis Pendayagunaan Wakaf": ["H. Herutoyo, SP", "Drs. H. M. Nadjib", "Ir. Farid Kusairi", "Junaidi S. Sos"],
    "Majelis Kader dan Sumber Daya Insani": ["Nur Wahyudi, ST", "Drs. Suparman", "Ahmad Haedar, S.Sos.I, M.Si", "Agus Mardiyanto, S.Ag"],
    "Majelis Pembinaan Kesejahteraan Sosial": ["Nursiswanta, SH", "Muh. Karim Amrullah, S.Ag", "Ahmad Ghozi, SE", "Khoirul Zaki, S.Pd"],
    "Majelis Ekonomi, Bisnis, dan Pariwisata": ["Anton Sudarto, S.Sos", "Suharyanto, S.Sos", "Saiful Bahri", "Ihsan Efendi, A.Md"],
    "Majelis Penelitian, Pengembangan, dan Teknologi Informasi": ["H. Muhammad Wazid, S.Ag, MA", "Drs. Atang Basuki", "Anton Rahmat Widodo, ST, MT", "H. M. Bunyamin Adib, SHI"],
}
JABATAN_MAJELIS = ["Ketua", "Wakil Ketua", "Sekretaris 1", "Sekretaris 2"]

# (nama, ketua, alamat, telepon) -- isi setelah data ranting diverifikasi (lihat https://muhammadiyahmoyudan.or.id/ranting/)
RANTING = []

# Nama dari halaman program kerja PCM; deskripsi dikosongkan sampai ada sumbernya.
AMAL_USAHA = [
    ("SMP Muhammadiyah 1 Moyudan", "pendidikan"),
    ("Klinik Pratama Aisyiyah", "kesehatan"),
    ("Panti Asuhan Ashabul Kahfi", "sosial"),
    ("AmbulanMu", "sosial"),
    ("LazisMu Moyudan", "sosial"),
    ("TOKOMU melalui MBC Moyudan", "ekonomi"),
]

# (judul, ringkasan, isi, tanggal_terbit aware datetime) -- salin dari /news/ dengan tanggal aslinya
BERITA = []

TAUTAN = [
    ("PP Muhammadiyah", "https://muhammadiyah.or.id"),
    ("Website resmi Muhammadiyah Moyudan", "https://muhammadiyahmoyudan.or.id"),
    # TODO: tambahkan PWM DIY dan PDM Sleman setelah URL-nya dicek bisa dibuka.
]


class Command(BaseCommand):
    help = "Mengisi data riil PCM Moyudan ke database."

    def add_arguments(self, parser):
        parser.add_argument("--tanpa-gambar", action="store_true", help="Jangan unduh gambar hero.")

    def handle(self, *args, **opts):
        profil, _ = Profil.objects.get_or_create(pk=1, defaults={"nama": "Pimpinan Cabang Muhammadiyah Moyudan", "nama_singkat": "PCM Moyudan"})
        profil.nama = "Pimpinan Cabang Muhammadiyah Moyudan"
        profil.nama_singkat = "PCM Moyudan"
        profil.tagline = "Persyarikatan Muhammadiyah di Moyudan, Sleman"
        profil.tentang = (
            "Pimpinan Cabang Muhammadiyah (PCM) Moyudan memimpin Muhammadiyah di wilayah Moyudan, Sleman, "
            "Daerah Istimewa Yogyakarta. Periode kepemimpinan saat ini 2022–2027, dengan majelis di bidang "
            "tabligh, pendidikan, kesehatan, wakaf, kader, kesejahteraan sosial, ekonomi, serta penelitian dan teknologi informasi."
        )
        # Belum ada sumber terverifikasi: biarkan kosong (tampil "Belum tersedia") bila belum diisi.
        profil.sejarah = profil.sejarah or ""
        profil.visi = profil.visi or ""
        profil.misi = profil.misi or ""
        profil.alamat_sekretariat = profil.alamat_sekretariat or ""
        profil.save()

        if not opts["tanpa_gambar"] and not profil.gambar_utama:
            try:
                req = urllib.request.Request(HERO_URL, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    profil.gambar_utama.save("pimpinan-pcm-2022-2027.jpg", ContentFile(r.read()), save=True)
                self.stdout.write("Gambar hero diunduh.")
            except Exception as e:  # jaringan mati dsb. tidak boleh menggagalkan seed
                self.stderr.write(f"Gambar hero dilewati ({e}).")

        urutan = 0

        def tambah(nama, jabatan, bagian):
            nonlocal urutan
            urutan += 1
            Pimpinan.objects.update_or_create(
                nama=nama, jabatan=jabatan, bagian=bagian, defaults={"periode": "2022–2027", "urutan": urutan}
            )

        for nama in PENASEHAT:
            tambah(nama, "Penasehat", "Penasehat")
        for jabatan, nama in INTI:
            tambah(nama, jabatan, "Pengurus Inti")
        for majelis, orang in MAJELIS.items():
            for jabatan, nama in zip(JABATAN_MAJELIS, orang):
                tambah(nama, f"{jabatan} {majelis}", majelis)

        for nama, ketua, alamat, telepon in RANTING:
            Ranting.objects.update_or_create(nama=nama, defaults={"ketua": ketua, "alamat": alamat, "telepon": telepon})
        for nama, bidang in AMAL_USAHA:
            AmalUsaha.objects.get_or_create(nama=nama, defaults={"bidang": bidang})
        for judul, ringkasan, isi, tanggal in BERITA:
            Berita.objects.get_or_create(judul=judul, defaults={"ringkasan": ringkasan, "isi": isi, "tanggal_terbit": tanggal, "status": Berita.Status.TERBIT})
        for i, (nama, url) in enumerate(TAUTAN, 1):
            TautanTerkait.objects.update_or_create(nama=nama, defaults={"url": url, "urutan": i})

        self.stdout.write(self.style.SUCCESS("Seed PCM Moyudan selesai."))
