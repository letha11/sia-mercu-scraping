
# MVP - Backend
1. Login
2. get absensi
3. Matkul

# MVP - Frontend (Mobile)
1. Login
2. Melihat absensi, materi, matkul, modul
3. Cache (jika server SIA lagi down, nanti tetep bisa nampilin hanya saja jika ada update saat server SIA down, kita tidak bisa mendapatkan pembaruan tersebut hingga refresh)

# Running this application locally
```bash
$ python app.py
```

# Response Example
## Jadwal
```json
{
  'periode': [
    {
      'label': Gasal 2022,
      'value': 20221
      'selected': false,
    },
    {
      'label': Genap 2022,
      'value': 20223
      'selected': false,
    },
    {
      'label': Gasal 2023,
      'value': 20231
      'selected': true,
    },
    ...
  ],
  'mata_kuliah': [
    {
      'hari': 'Rabu',
      'time': '07:30-10:00' (mulai-selesai),
      'nama_matkul': 'Aljabar Linier',
      'ruangan': 'C-421',
      'daring': false,
      'dosen': 'Achmad Kodar, Drs. MT'
    },
    {
      'hari': 'Rabu',
      'time': '10:15-12:45' (mulai-selesai),
      'nama_matkul': 'Pemrograman PL/SQL',
      'ruangan': 'D-205',
      'daring': false,
      'dosen': 'Sabar Rudiarto, M.Kom'
    },
    ...
  ]
}
```

## Home ? or Absen ?
```json
{
    'mata_kuliah': [
        {
            'nama_matkul': 'Aljabar Linear',
            'perkuliahan': [
                {
                    'pertemuan': 1,
                    'tanggal': 'Rab, 6 Sep 2023',
                    'kehadiran': 'Hadir' or 'Tidak Hadir' or 'Belum Dilaksanakan',
                    'materi': 'Sub-CPMK 1.1 Mampu menjelaskan system bilangan (CPMK 1), Materi : Pengantar sistem persamaan linear dan SPL',
                    'link_modul': 'http://modul.mercubuana.ac.id/eDBDTXhBRE13RWpNMUV6Vg==/'
                },
                {
                    'pertemuan': 2,
                    'tanggal': 'Rab, 13 Sep 2023',
                    'kehadiran': 'Tidak Hadir',
                    'materi': '	Sub-CPMK 1.2. Mampu memahami daerah asal dan daerah hasil suatu grafik (CPMK 1), Materi : Operasi Baris Elementer dan Eliminasi Gauss Jordan',
                    'link_modul': 'http://modul.mercubuana.ac.id/eTBDTXhBRE13RWpNMUV6Vg==/'
                },
                ...
            ],
        }
        ...
    ]
}
```
