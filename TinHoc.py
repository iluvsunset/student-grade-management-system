
ho_ten = input("Nhập họ tên học sinh: ")


diem_toan = float(input("Nhập điểm Toán: "))
diem_van = float(input("Nhập điểm Ngữ văn: "))
diem_tin = float(input("Nhập điểm Tin học: "))


dtb = (diem_toan + diem_van + diem_tin) / 3

if dtb >= 8.0:
    xep_loai = "Giỏi"
elif 6.5 <= dtb < 8.0:
    xep_loai = "Khá"
elif 5.0 <= dtb < 6.5:
    xep_loai = "Trung bình"
else:
    xep_loai = "Yếu"


print("\n--- KẾT QUẢ HỌC TẬP ---")
print("Họ tên học sinh:", ho_ten)
print("Điểm trung bình:", round(dtb, 2))
print("Xếp loại học lực:", xep_loai)