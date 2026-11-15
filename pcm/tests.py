from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Berita, PesanMasuk, Profil


def buat_berita(judul="Judul", **kw):
    data = dict(judul=judul, ringkasan="Ringkasan", isi="Isi berita", status=Berita.Status.TERBIT,
                tanggal_terbit=timezone.now() - timedelta(hours=1))
    data.update(kw)
    return Berita.objects.create(**data)


class PcmTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Profil.objects.create(nama="PCM Uji", nama_singkat="PCM")

    def test_halaman_publik_200(self):
        berita = buat_berita()
        for nama in ["beranda", "profil", "pimpinan", "ranting", "amal_usaha", "berita_list", "agenda", "unduhan", "kontak"]:
            self.assertEqual(self.client.get(reverse(f"pcm:{nama}")).status_code, 200, nama)
        self.assertEqual(self.client.get(berita.get_absolute_url()).status_code, 200)

    def test_berita_draf_404(self):
        b = buat_berita(status=Berita.Status.DRAF)
        self.assertEqual(self.client.get(b.get_absolute_url()).status_code, 404)

    def test_berita_masa_depan_404(self):
        b = buat_berita(tanggal_terbit=timezone.now() + timedelta(days=2))
        self.assertEqual(self.client.get(b.get_absolute_url()).status_code, 404)

    def test_slug_tetap_unik(self):
        a, b = buat_berita("Judul Sama"), buat_berita("Judul Sama")
        self.assertNotEqual(a.slug, b.slug)

    def test_manager_terbit(self):
        buat_berita("A")
        buat_berita("B", status=Berita.Status.DRAF)
        self.assertEqual(Berita.objects.terbit().count(), 1)

    def test_paginasi_6_per_halaman(self):
        for i in range(7):
            buat_berita(f"Berita {i}")
        r = self.client.get(reverse("pcm:berita_list"))
        self.assertEqual(len(r.context["halaman"]), 6)

    def test_formulir_kontak_menyimpan_pesan(self):
        r = self.client.post(reverse("pcm:kontak"), {"nama": "Budi", "email": "b@x.id", "subjek": "Halo", "pesan": "Pesan uji yang cukup panjang."}, follow=True)
        self.assertEqual(PesanMasuk.objects.count(), 1)
        self.assertContains(r, "sudah terkirim")

    def test_formulir_kontak_menolak_pesan_pendek(self):
        self.client.post(reverse("pcm:kontak"), {"nama": "Budi", "email": "b@x.id", "subjek": "Halo", "pesan": "pendek"})
        self.assertEqual(PesanMasuk.objects.count(), 0)

    def test_profil_hanya_satu_baris(self):
        with self.assertRaises(ValidationError):
            Profil.objects.create(nama="Kedua", nama_singkat="K")

    def test_pencarian_berita(self):
        buat_berita("Pengajian Ahad Pagi")
        buat_berita("Kerja bakti")
        r = self.client.get(reverse("pcm:berita_list"), {"q": "pengajian"})
        self.assertEqual([b.judul for b in r.context["halaman"]], ["Pengajian Ahad Pagi"])
