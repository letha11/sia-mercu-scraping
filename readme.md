# Sia Mercubuana Website Scraping

# Usage
1. clone this repository
```bash
$ git clone 
```
2. Install all required packages
```bash
$ pip install -r requirements.txt
```
3. Start the app
```bash
$ python app.py
```
4. Visit http://localhost:5000/api

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

## Home
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
