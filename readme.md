# Tugas-Teknologi-Sistem-Terintegrasi

## Penjelasan Microservice
Microservice yang diambil yaitu merupakan core dari bisnis yang dibuat yaitu jasa konsultasi desain halaman rumah. Ketika pengguna ingin memesan data akan masuk ke tabel desain, permintaan, dan konsuldesain. Pengguna melakukan konsultasi dengan melihat data yang tersedia yaitu nama desainer dan no hp desainer yang terdapat pada tabel konsuldesain. Tipe desain yang dipilih akan terdapat pada tabel desain. Selain itu, terdapat juga deskripsi, tanggal pesan, dan status pesanan pada tabel desain. Id dan id desainer di generate secara otomatis ketika pengguna melakukan aktivitas POST.

## Berikut merupakan cara melakukan setup container di docker
docker build -t demo-desain .
docker run -d --name demo-konsul-desain -p 80:80 demo-desain

Keterangan: 
- Penjelasan lebih lanjut terdapat di file dokumen.
- Saat pertama kali membuka website, proses login atau register akan cukup lama jadi disarankan menunggu sekitar 10-15 detik saat website pertama kali dibuka
