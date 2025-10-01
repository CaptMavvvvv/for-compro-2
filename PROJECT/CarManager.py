import struct
from collections import defaultdict
import os
import datetime
from typing import Dict, Any, Tuple, Optional, List

# ==============================================================================
# 1.Constants สำหรับ 3 Entities
# ==============================================================================

# Car: < ?i30s10sd (IsActive, ID, Model, Plate, Rate) -> 53 bytes
CAR_FORMAT = '< ?i30s10sd'
CAR_FILE_NAME = 'cars.bin'
CAR_ENCODING = 'utf-8'

# Customer: < ?i30s15s (IsActive, ID, Name, Phone) -> 50 bytes
CUSTOMER_FORMAT = '< ?i50s15s'
CUSTOMER_FILE_NAME = 'customers.bin'
CUSTOMER_ENCODING = 'utf-8'

# Rental: < ?iiidid (7 fields: IsActive, R_ID, C_ID, Car_ID, StartDate(i), EndDate(i), TotalPrice(d))
RENTAL_FORMAT = '< ?iiiiid' 
RENTAL_FILE_NAME = 'rentals.bin'
RENTAL_ENCODING = 'utf-8' 
# ==============================================================================
# 2.Base Manager
# ==============================================================================

class FileManager:
    """คลาสจัดการไฟล์ไบนารีพื้นฐาน: จัดการการเข้าถึงไฟล์, Free Space, และ CRUD ตรรกะทั่วไป"""
    
    def __init__(self, format_string: str, filename: str, encoding: str):
        self.format = format_string
        self.filename = filename
        self.encoding = encoding
        self.record_size = struct.calcsize(format_string)
        
        try:
            self.file = open(self.filename, 'r+b')
            print(f"File '{self.filename}' opened for R/W.")
        except FileNotFoundError:
            self.file = open(self.filename, 'w+b') 
            print(f"File '{self.filename}' created and opened for R/W.")
        self.file.seek(0, os.SEEK_SET)

    def close(self):
        """ปิดและซิงค์ไฟล์อย่างปลอดภัย (Exit Hook)"""
        self.file.flush()
        os.fsync(self.file.fileno())
        self.file.close()
    

    # --- Utility Overrides ---

    def _pack_record(self, data: Dict[str, Any]) -> bytes:
        raise NotImplementedError("Subclass must implement _pack_record.")

    def _unpack_record(self, record_bytes: bytes) -> Dict[str, Any]:
        raise NotImplementedError("Subclass must implement _unpack_record.")

    # --- CRUD Base Logic ---

    def add_record(self, data: Dict[str, Any]) -> int:
        """C - เพิ่มระเบียน (ค้นหาช่องว่างก่อน)"""
        data['IsActive'] = True
        packed_data = self._pack_record(data)

        self.file.seek(0, os.SEEK_SET)
        
        while True:
            current_offset = self.file.tell() 
            
            status_byte = self.file.read(1)
            if not status_byte: break
            
            remaining_bytes = self.file.read(self.record_size - 1)
            if len(remaining_bytes) < self.record_size - 1:
                break
            
            is_active = struct.unpack('< ?', status_byte)[0]
            
            if not is_active:
                self.file.seek(current_offset, os.SEEK_SET) 
                self.file.write(packed_data)
                self.file.flush()
                print(f"✅ Reusing free space at offset: {current_offset} bytes in {self.filename}.")
                return current_offset
            
        self.file.seek(0, os.SEEK_END)
        offset = self.file.tell()
        self.file.write(packed_data)
        self.file.flush()
        print(f"➕ Appended new record at offset: {offset} bytes in {self.filename}.")
        return offset

    def get_record_by_id(self, record_id: int) -> Optional[Tuple[Dict[str, Any], int]]:
        self.file.seek(0, os.SEEK_SET)
        offset = 0
        
        while True:
            record_bytes = self.file.read(self.record_size)
            if len(record_bytes) < self.record_size: 
                break
            
            try:
                record_data = self._unpack_record(record_bytes)
                if record_data['IsActive'] and record_data['ID'] == record_id:
                    return record_data, offset
            except struct.error: pass 
            
            offset += self.record_size
        return None

    def update_record(self, record_id: int, new_data: Dict[str, Any]) -> bool:
        """U - แก้ไขระเบียน"""
        result = self.get_record_by_id(record_id)
        if result is None:
            print(f"❌ Error: ID {record_id} not found or is inactive in {self.filename}.")
            return False
        
        old_data, offset = result
        updated_data = old_data.copy()
        if 'EndDate' not in updated_data:
             updated_data['EndDate'] = 0 

        updated_data.update(new_data)
        updated_data['ID'] = record_id
        updated_data['IsActive'] = old_data['IsActive'] 
        updated_data.update(new_data)
        updated_data['ID'] = record_id
        updated_data['IsActive'] = old_data['IsActive'] 
        
        packed_data = self._pack_record(updated_data)
        
        self.file.seek(offset, os.SEEK_SET)
        self.file.write(packed_data)
        self.file.flush()
        
        print(f"📝 Successfully updated ID {record_id} at offset {offset} in {self.filename}.")
        return True

    def delete_record(self, record_id: int) -> bool:
        """D - ลบแบบ Soft Delete"""
        result = self.get_record_by_id(record_id)
        if result is None:
            print(f"❌ Error: ID {record_id} not found or already deleted in {self.filename}.")
            return False
        
        _, offset = result
        deleted_flag_bytes = struct.pack('< ?', False)
        
        self.file.seek(offset, os.SEEK_SET)
        self.file.write(deleted_flag_bytes)
        self.file.flush()
        
        print(f"🗑️ Soft deleted ID {record_id} at offset {offset} in {self.filename}.")
        return True

    def get_all_records(self) -> List[Dict[str, Any]]:
        active_records = []
        self.file.seek(0, os.SEEK_SET)
        while True:
            record_bytes = self.file.read(self.record_size)
            if len(record_bytes) < self.record_size:
                break
            
            try:
                record_data = self._unpack_record(record_bytes)
                if record_data['IsActive']:
                    active_records.append(record_data)
            except struct.error: pass
        return active_records

# ==============================================================================
# 3.Minimal Overrides
# ==============================================================================

class CarManager(FileManager):
    def __init__(self):
        super().__init__(CAR_FORMAT, CAR_FILE_NAME, CAR_ENCODING)
    
    def _pack_record(self, data: Dict[str, Any]) -> bytes:
        model_bytes = data['Model'].encode(self.encoding).ljust(30, b'\x00')
        license_bytes = data['LicensePlate'].encode(self.encoding).ljust(10, b'\x00')
        
        return struct.pack(
            self.format,
            data.get('IsActive', True),
            data['ID'],
            model_bytes,
            license_bytes,
            data['DailyRate']
        )

    def _unpack_record(self, record_bytes: bytes) -> Dict[str, Any]:
        unpacked_data = struct.unpack(self.format, record_bytes)
        model = unpacked_data[2].split(b'\x00', 1)[0].decode(self.encoding, errors='ignore').strip()
        license_plate = unpacked_data[3].split(b'\x00', 1)[0].decode(self.encoding, errors='ignore').strip()
        
        return {
            'IsActive': unpacked_data[0],
            'ID': unpacked_data[1],
            'Model': model,
            'LicensePlate': license_plate,
            'DailyRate': unpacked_data[4]
        }
class CustomerManager(FileManager):
    def __init__(self):
        super().__init__(CUSTOMER_FORMAT, CUSTOMER_FILE_NAME, CUSTOMER_ENCODING)
    
    def _pack_record(self, data: Dict[str, Any]) -> bytes:
        name_bytes = data['Name'].encode(self.encoding).ljust(50, b'\x00')
        phone_bytes = data['Phone'].encode(self.encoding).ljust(15, b'\x00')
        
        return struct.pack(
            self.format,
            data.get('IsActive', True),
            data['ID'],
            name_bytes,
            phone_bytes
        )

    def _unpack_record(self, record_bytes: bytes) -> Dict[str, Any]:
        unpacked_data = struct.unpack(self.format, record_bytes)
        
        name = unpacked_data[2].split(b'\x00', 1)[0].decode(self.encoding, errors='ignore').strip()
        phone = unpacked_data[3].split(b'\x00', 1)[0].decode(self.encoding, errors='ignore').strip()
        
        return {
            'IsActive': unpacked_data[0],
            'ID': unpacked_data[1],
            'Name': name,
            'Phone': phone
        }

class RentalManager(FileManager):
    def __init__(self):
        super().__init__(RENTAL_FORMAT, RENTAL_FILE_NAME, RENTAL_ENCODING)
    
    def _pack_record(self, data: Dict[str, Any]) -> bytes:
        return struct.pack(
            self.format,
            data.get('IsActive', True),  # 1. ?
            int(data['ID']),             # 2. i
            int(data['CustomerID']),     # 3. i
            int(data['CarID']),          # 4. i
            int(data['StartDate']),      # 5. i
            int(data.get('EndDate', 0)), # 6. i
            float(data['TotalPrice'])    # 7. d
        )

    def _unpack_record(self, record_bytes: bytes) -> Dict[str, Any]:
        unpacked_data = struct.unpack(self.format, record_bytes)

        return {
            'IsActive': unpacked_data[0],
            'ID': unpacked_data[1],
            'CustomerID': unpacked_data[2],
            'CarID': unpacked_data[3],
            'StartDate': unpacked_data[4],
            'EndDate': unpacked_data[5],
            'TotalPrice': unpacked_data[6]
        }
    
# ==============================================================================
# 4.Utility สำหรับเมนูและการจัดการอินพุต
# ==============================================================================

def get_user_choice(prompt: str, valid_choices: List[str]) -> str:
    """รับอินพุตจากผู้ใช้และตรวจสอบว่าอยู่ในตัวเลือกที่กำหนดหรือไม่"""
    while True:
        choice = input(prompt).strip().upper()
        if choice in valid_choices:
            return choice
        print("❌ ตัวเลือกไม่ถูกต้อง กรุณาเลือกใหม่")

def get_int_input(prompt: str) -> int:
    # ฟังก์ชันจำลองสำหรับคำนวณวัน
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("❌ กรุณาป้อนเฉพาะตัวเลขจำนวนเต็มเท่านั้น")

def get_float_input(prompt: str) -> float:
    """รับอินพุตเป็นตัวเลขทศนิยม (DailyRate, TotalPrice)"""
    while True:
        try:
            return float(input(prompt).strip())
        except ValueError:
            print("❌ กรุณาป้อนเฉพาะตัวเลขเท่านั้น")

def get_date_input(prompt: str) -> int:
    """รับอินพุตวันที่และแปลงเป็น DDMMYYYY int"""
    while True:
        date_str = input(prompt).strip() 
        if len(date_str) == 8 and date_str.isdigit():
            try:
                datetime.datetime.strptime(date_str, '%d%m%Y') 
                return int(date_str)
            except ValueError:
                print("❌ รูปแบบวันที่ไม่ถูกต้อง")
        else:
            print("❌ รูปแบบไม่ถูกต้อง กรุณาป้อนเป็น DDMMYYYY เช่น 25102025")

def generate_master_report(car_mgr: 'CarManager', cust_mgr: 'CustomerManager', rental_mgr: 'RentalManager', report_filename: str = 'master_report.txt'):
    """สร้างไฟล์รายงานรวมที่แสดงข้อมูล Active ทั้งหมดจากทุก Manager"""
    
    report_content = []
    
    title = "MASTER RENTAL SYSTEM REPORT"
    report_content.append("=" * 70)
    report_content.append(f"{' ' * ((70 - len(title)) // 2)}{title}")
    report_content.append("=" * 70)
    report_content.append(f"Generated On: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_content.append("-" * 70)
    
    report_content.append("\n\n--- 🚗 ACTIVE CAR INVENTORY ---")
    car_fields = [('ID', 5), ('Model', 30), ('LicensePlate', 15), ('DailyRate', 12)]
    car_records = car_mgr.get_all_records()
    report_content.append(f"Total Active Cars: {len(car_records)}")
    
    header_line = ' | '.join(f"{name:<{length}}" for name, length in car_fields)
    report_content.append(header_line)
    report_content.append("-" * (sum(length for _, length in car_fields) + len(car_fields) * 3))
    
    if car_records:
        for car in car_records:
            line_parts = []
            for field_name, length in car_fields:
                value = car.get(field_name, '')
                if isinstance(value, float):
                    line_parts.append(f"{value:.2f}".ljust(length))
                else:
                    line_parts.append(f"{str(value):<{length}}")
            report_content.append(' | '.join(line_parts))
    else:
        report_content.append("No active cars found.")
        
    report_content.append("\n\n--- 🧑 ACTIVE CUSTOMER DIRECTORY ---")
    cust_fields = [('ID', 5), ('Name', 45), ('Phone', 15)] # ใช้ 45s สำหรับชื่อที่ยาวขึ้น
    cust_records = cust_mgr.get_all_records()
    report_content.append(f"Total Active Customers: {len(cust_records)}")
    
    header_line = ' | '.join(f"{name:<{length}}" for name, length in cust_fields)
    report_content.append(header_line)
    report_content.append("-" * (sum(length for _, length in cust_fields) + len(cust_fields) * 3))
    
    if cust_records:
        for cust in cust_records:
            line_parts = []
            for field_name, length in cust_fields:
                value = cust.get(field_name, '')
                line_parts.append(f"{str(value):<{length}}")
            report_content.append(' | '.join(line_parts))
    else:
        report_content.append("No active customers found.")

    report_content.append("\n\n--- 🧾 ACTIVE RENTAL AGREEMENTS ---")
    rental_fields = [('ID', 5), ('CustomerID', 10), ('CarID', 7), ('StartDate', 10), ('Days', 5), ('TotalPrice', 12)]
    rental_records = rental_mgr.get_all_records()
    report_content.append(f"Total Active Rentals: {len(rental_records)}")
    
    header_line = ' | '.join(f"{name:<{length}}" for name, length in rental_fields)
    report_content.append(header_line)
    report_content.append("-" * (sum(length for _, length in rental_fields) + len(rental_fields) * 3))
    
    if rental_records:
        for rent in rental_records:
            line_parts = []
            for field_name, length in rental_fields:
                value = rent.get(field_name, '')
                if isinstance(value, float):
                    line_parts.append(f"{value:.2f}".ljust(length))
                elif field_name == 'StartDate':
                     # แสดง StartDate (DDMMYYYY)
                     line_parts.append(f"{value}".ljust(length)) 
                else:
                    line_parts.append(f"{str(value):<{length}}")
            report_content.append(' | '.join(line_parts))
    else:
        report_content.append("No active rental agreements found.")

    report_content.append("\n" + "=" * 70)
    
    try:
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_content) + '\n')
        print(f"\n📄 รายงานรวม (Master Report) ถูกสร้างสำเร็จที่ '{report_filename}'.")
    except IOError as e:
        print(f"❌ Error writing master report file: {e}")

# ==============================================================================
# 5. ฟังก์ชันเมนูย่อยสำหรับแต่ละ Module
# ==============================================================================

def run_car_menu(manager: CarManager):
    while True:
        print("\n=== [1] จัดการข้อมูลรถยนต์ ===")
        print("A: เพิ่มรถยนต์ | U: แก้ไข | D: ลบ (Soft Delete)")
        print("V: ดูทั้งหมด | S: ค้นหาด้วย ID")
        print("X: กลับสู่เมนูหลัก")
        
        choice = get_user_choice(">> กรุณาเลือก: ", ['A', 'U', 'D', 'V', 'S', 'X'])

        if choice == 'A':
            print("\n-- เพิ่มรถยนต์ --")
            car_id = get_int_input("ID รถยนต์: ")
            model = input("รุ่นรถยนต์ (สูงสุด 30 ตัวอักษร): ").strip()[:30]
            plate = input("ป้ายทะเบียน (สูงสุด 10 ตัวอักษร): ").strip()[:10]
            rate = get_float_input("อัตราค่าเช่าต่อวัน: ")
            manager.add_record({'ID': car_id, 'Model': model, 'LicensePlate': plate, 'DailyRate': rate})

        elif choice == 'U':
            print("\n-- แก้ไขรถยนต์ --")
            car_id = get_int_input("ID รถยนต์ที่ต้องการแก้ไข: ")
            rate = get_float_input("อัตราค่าเช่าต่อวันใหม่: ")
            manager.update_record(car_id, {'DailyRate': rate})

        elif choice == 'D':
            print("\n-- ลบรถยนต์ --")
            car_id = get_int_input("ID รถยนต์ที่ต้องการลบ (Soft Delete): ")
            manager.delete_record(car_id)

        elif choice == 'V':
            print("\n-- รายการรถยนต์ทั้งหมด (Active) --")
            cars = manager.get_all_records()
            if not cars:
                print("ไม่มีข้อมูลรถยนต์ที่ใช้งานอยู่")
            else:
                for car in cars:
                    print(f"ID: {car['ID']} | Model: {car['Model']:<30} | Plate: {car['LicensePlate']:<10} | Rate: {car['DailyRate']:.2f}")

        elif choice == 'S':
            print("\n-- ค้นหารถยนต์ด้วย ID --")
            car_id = get_int_input("ID รถยนต์ที่ต้องการค้นหา: ")
            
            result = manager.get_record_by_id(car_id) 
            
            if result is not None:
                car, offset = result
                print(f"✅ พบข้อมูล: ID: {car['ID']} | Model: {car['Model']} | Plate: {car['LicensePlate']} | Rate: {car['DailyRate']:.2f} (Offset: {offset} bytes)")
            else:
                print("❌ ไม่พบรถยนต์ ID นี้ หรือรถยนต์ถูกลบไปแล้ว")

        elif choice == 'X':
            break

def run_customer_menu(manager: CustomerManager):
    while True:
        print("\n=== [2] จัดการข้อมูลลูกค้า ===")
        print("A: เพิ่มลูกค้า | U: แก้ไข | D: ลบ (Soft Delete)")
        print("V: ดูทั้งหมด | S: ค้นหาด้วย ID")
        print("X: กลับสู่เมนูหลัก")
        
        choice = get_user_choice(">> กรุณาเลือก: ", ['A', 'U', 'D', 'V', 'S', 'X'])
        
        if choice == 'A':
            print("\n-- เพิ่มลูกค้า --")
            cust_id = get_int_input("ID ลูกค้า: ")
            name = input("ชื่อ-นามสกุล (สูงสุด 30 ตัวอักษร): ").strip()[:30]
            phone = input("เบอร์โทรศัพท์ (สูงสุด 15 ตัวอักษร): ").strip()[:15]
            manager.add_record({'ID': cust_id, 'Name': name, 'Phone': phone})

        elif choice == 'U':
            print("\n-- แก้ไขเบอร์โทรศัพท์ลูกค้า --")
            cust_id = get_int_input("ID ลูกค้าที่ต้องการแก้ไข: ")
            phone = input("เบอร์โทรศัพท์ใหม่: ").strip()[:15]
            manager.update_record(cust_id, {'Phone': phone})

        elif choice == 'D':
            print("\n-- ลบลูกค้า --")
            cust_id = get_int_input("ID ลูกค้าที่ต้องการลบ (Soft Delete): ")
            manager.delete_record(cust_id)
            
        elif choice == 'V':
            print("\n-- รายชื่อลูกค้าทั้งหมด (Active) --")
            customers = manager.get_all_records()
            if not customers:
                print("ไม่มีข้อมูลลูกค้าที่ใช้งานอยู่")
            else:
                for cust in customers:
                    print(f"ID: {cust['ID']} | Name: {cust['Name']:<30} | Phone: {cust['Phone']}")
        
        elif choice == 'S':
            print("\n-- ค้นหาลูกค้าด้วย ID --")
            cust_id = get_int_input("ID ลูกค้าที่ต้องการค้นหา: ")
            
            result = manager.get_record_by_id(cust_id)
            
            if result is not None:
                cust, offset = result
                print(f"✅ พบข้อมูล: ID: {cust['ID']} | Name: {cust['Name']} | Phone: {cust['Phone']} (Offset: {offset} bytes)")
            else:
                print("❌ ไม่พบลูกค้า ID นี้ หรือลูกค้าถูกลบไปแล้ว")

        elif choice == 'X':
            break

def run_rental_menu(manager: RentalManager, car_mgr: CarManager, cust_mgr: CustomerManager):
    while True:
        print("\n=== [3] จัดการสัญญาเช่า ===")
        print("A: สร้างสัญญา | V: ดูทั้งหมด | S: ค้นหาด้วย ID")
<<<<<<< HEAD:PROJECT/Rental Program.py
        print("D: คืนรถ (Soft Delete)")
        print("X: กลับสู่เมนูหลัก")
        
        choice = get_user_choice(">> กรุณาเลือก: ", ['A', 'V', 'D', 'S', 'X'])
=======
        print("D: คืนรถ (Soft Delete) | R: สร้างรายงานสรุป (.txt)")
        print("L: สร้างรายงานรายละเอียดสัญญาเช่า (.txt)") 
        print("X: กลับสู่เมนูหลัก")
        
        choice = get_user_choice(">> กรุณาเลือก: ", ['A', 'V', 'D', 'S', 'R', 'L', 'X'])
>>>>>>> 69bfc037f7880797c02da484f014d7fe289f2c67:PROJECT/CarManager.py
        
        if choice == 'A':
            print("\n-- สร้างสัญญาเช่า --")
            rental_id = get_int_input("ID สัญญาเช่า: ")
            cust_id = get_int_input("ID ลูกค้า: ")
            car_id = get_int_input("ID รถยนต์: ")
            
            if not cust_mgr.get_record_by_id(cust_id):
                print("❌ ID ลูกค้าไม่ถูกต้อง หรือลูกค้าถูกลบไปแล้ว")
                continue
            car_result = car_mgr.get_record_by_id(car_id)
            if not car_result:
                print("❌ ID รถยนต์ไม่ถูกต้อง หรือรถถูกเช่าอยู่/ถูกลบไปแล้ว")
                continue
            
            car_data, _ = car_result
            daily_rate = car_data['DailyRate']
            
            start_date_int = get_date_input("วันที่เริ่มเช่า (DDMMYYYY): ")
            end_date_int = get_date_input("วันที่สิ้นสุดการเช่า (DDMMYYYY): ")

            try:
                start_date_str = str(start_date_int).zfill(8)
                end_date_str = str(end_date_int).zfill(8)
                start_date_obj = datetime.datetime.strptime(start_date_str, '%d%m%Y')
                end_date_obj = datetime.datetime.strptime(end_date_str, '%d%m%Y')
                
                print(f"  🗓️ วันที่เช่า: {start_date_obj.strftime('%d-%m-%Y')} ถึง {end_date_obj.strftime('%d-%m-%Y')}")
                
                days = (end_date_obj - start_date_obj).days + 1 
                total_price = daily_rate * days
                print(f"✅ คำนวณจำนวนวันเช่า: {days} วัน")
            except ValueError:
                print("❌ ข้อผิดพลาดในการคำนวณวันที่ ใช้ราคาเช่า 1 วันเป็นค่าเริ่มต้น")
                total_price = daily_rate 
                days = 1

            print(f"✅ คำนวณราคารวม: {daily_rate:.2f} * {days} วัน = {total_price:.2f} บาท")
            
            manager.add_record({
                'ID': rental_id, 'CustomerID': cust_id, 'CarID': car_id, 
                'StartDate': start_date_int, 
                'EndDate': end_date_int,
                'TotalPrice': total_price
            })

            car_mgr.update_record(car_id, {'IsRented': True}) 
            print(f"✅ สร้างสัญญาเช่า ID {rental_id} และอัปเดตสถานะรถ ID {car_id} เป็น 'ถูกเช่าแล้ว' เรียบร้อย.")

        elif choice == 'V':
            print("\n-- รายการสัญญาเช่าทั้งหมด (Active) --")
            rentals = manager.get_all_records()
            if not rentals:
                print("ไม่มีสัญญาเช่าที่ใช้งานอยู่")
            else:
                for rent in rentals:
                    start_date_display = format_date_display(rent.get('StartDate', 0))
                    end_date_display = format_date_display(rent.get('EndDate', 0))

                    print(f"ID: {rent['ID']} | CustID: {rent['CustomerID']} | CarID: {rent['CarID']} | Start: {start_date_display} | End: {end_date_display} | Total: {rent['TotalPrice']:.2f}")

        

        elif choice == 'D':
            print("\n-- ปิด/คืนสัญญาเช่า (Soft Delete) --")
            rental_id = get_int_input("ID สัญญาเช่าที่ต้องการคืนรถ: ")
            
            result = manager.get_record_by_id(rental_id)
            if result is None:
                print(f"❌ ไม่พบสัญญาเช่า ID {rental_id} หรือถูกปิดไปแล้ว.")
                return

            rent_data, _ = result
            car_id = rent_data['CarID']
            
            if manager.delete_record(rental_id):
                print(f"✅ สัญญาเช่า ID {rental_id} ถูกปิดเรียบร้อยแล้ว (Soft Deleted).")
                
                car_mgr.update_record(car_id, {'IsRented': False})
                print(f"✅ อัปเดตสถานะรถ ID {car_id} เป็น 'ว่างให้เช่า' เรียบร้อย.")
            else:
                print(f"❌ ไม่สามารถปิดสัญญาเช่า ID {rental_id} ได้.")

        elif choice == 'S':
            print("\n-- ค้นหาสัญญาเช่าด้วย ID --")
            rental_id = get_int_input("ID สัญญาเช่าที่ต้องการค้นหา: ")
            
            result = manager.get_record_by_id(rental_id)
            
            if result is not None:
                rent, _ = result 
                
                start_date_display = format_date_display(rent.get('StartDate', 0))
                end_date_display = format_date_display(rent.get('EndDate', 0))

                print(f"✅ พบข้อมูล: ID: {rent['ID']} | CustID: {rent['CustomerID']} | CarID: {rent['CarID']} | Start: {start_date_display} | End: {end_date_display} | Total: {rent['TotalPrice']:.2f}")
            else:
                print("❌ ไม่พบสัญญาเช่า ID นี้ หรือสัญญานี้ถูกปิดไปแล้ว")

<<<<<<< HEAD:PROJECT/Rental Program.py
        elif choice == 'X':
            break


def generate_detailed_summary_report(car_mgr: 'CarManager', cust_mgr: 'CustomerManager', rental_mgr: 'RentalManager', report_filename: str = 'detailed_summary_report.txt'):
    """
    สร้างรายงานสรุปที่รวมรายละเอียดรถยนต์ทั้งหมด (Active/Rented/Deleted) 
    พร้อมข้อมูลการเช่าที่เกี่ยวข้อง และส่วนสรุปสถิติ
    """
    
    all_car_records = car_mgr.get_all_records() #
    active_rentals = rental_mgr.get_all_records()
    rented_car_ids = {rent['CarID'] for rent in active_rentals}
    rental_by_car_id = {rent['CarID']: rent for rent in active_rentals}
=======
        elif choice == 'R':
            manager.generate_report(
                "RENTAL AGREEMENT SUMMARY", 
                [('ID', 5), ('CustomerID', 10), ('CarID', 7), ('StartDate', 10), ('Days', 5), ('TotalPrice', 12)], 
                'rental_report.txt'
            )
        
        elif choice == 'L':
            generate_rental_detail_report(manager, cust_mgr, car_mgr)

        elif choice == 'X':
            break

import struct
from collections import defaultdict
import datetime
import os
from typing import Dict, Any, Tuple, Optional, List

# --- ฟังก์ชัน Helper สำหรับการอ่านข้อมูลทั้งหมด (เหมือนเดิม) ---
def _get_all_records_from_manager(manager):
    records = []
    manager.file.seek(0, os.SEEK_SET)
    while True:
        record_bytes = manager.file.read(manager.record_size)
        if len(record_bytes) < manager.record_size: break
        try:
            records.append(manager._unpack_record(record_bytes))
        except struct.error: continue 
    return records

def generate_detailed_summary_report(car_mgr: 'CarManager', cust_mgr: 'CustomerManager', rental_mgr: 'RentalManager', report_filename: str = 'detailed_summary_report.txt'):
    """
    สร้างรายงานสรุปละเอียด (Rental Detail + Statistics)
    """
    
    # 1. รวบรวมข้อมูลและคำนวณสถิติ
    all_car_records = _get_all_records_from_manager(car_mgr)
    active_rentals = rental_mgr.get_all_records()
    rented_car_ids = {rent['CarID'] for rent in active_rentals} 
>>>>>>> 69bfc037f7880797c02da484f014d7fe289f2c67:PROJECT/CarManager.py
    
    total_cars = len(all_car_records)
    active_cars = [car for car in all_car_records if car['IsActive']]
    deleted_cars = total_cars - len(active_cars)
    currently_rented = len(rented_car_ids)
    available_now = len(active_cars) - currently_rented
    
    rate_list = [car['DailyRate'] for car in active_cars]
    min_rate = min(rate_list) if rate_list else 0.00
    max_rate = max(rate_list) if rate_list else 0.00
    avg_rate = sum(rate_list) / len(rate_list) if rate_list else 0.00
    
<<<<<<< HEAD:PROJECT/Rental Program.py
    cars_by_brand = {}
    for car in all_car_records:
        if car['IsActive'] and car['ID'] not in rented_car_ids:
            full_model_name = car['Model'].strip() 
            brand = full_model_name.split(' ')[0] 
            cars_by_brand[brand] = cars_by_brand.get(brand, 0) + 1
            
    report_content = []
    
    title_line = "Detailed Rental Summary Report"
    report_content.append("=" * 155)
    report_content.append(f"{' ' * ((150 - len(title_line)) // 2)}{title_line}")
    report_content.append("=" * 155)
    report_content.append(f"Generated At : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 
    report_content.append(f"Endianness   : Little-Endian")
    report_content.append(f"Time Zone    : +07:00 (Indochina Time)")
    report_content.append(f"Encoding     : UTF-8 (fixed-length)")
    report_content.append("-" * 155)
    
    fields = [
        ('Car ID', 6), ('Model', 20), ('Plate', 12), ('Rate', 10), 
        ('Status', 10), ('Rented', 8), 
        ('Cust ID', 8), ('Name', 30), ('Start Date', 10), ('End Date', 10) 
    ]
    
    header_line = ' | '.join(f"{name:<{length}}" for name, length in fields)
    
    report_content.append("ALL CARS DETAIL:") 
    report_content.append(header_line)
    report_content.append("-" * (sum(length for _, length in fields) + len(fields) * 3))

    for car_data in all_car_records: 
        car_id = car_data['ID']
        car_model = car_data['Model'].strip('\x00')
        car_plate = car_data.get('LicensePlate', 'N/A').strip('\x00')
        car_rate = car_data.get('DailyRate', 0.00)
        
        cust_id_display = ""
        cust_name = ""
        start_date_display = ""
        end_date_display = ""
        rented_flag = "No" 

        if not car_data['IsActive']:
            car_status_text = "DELETED" 
        elif car_id in rental_by_car_id:
            rent = rental_by_car_id[car_id]
            
            cust_result = cust_mgr.get_record_by_id(rent['CustomerID'])
            cust_name = cust_result[0]['Name'].strip('\x00') if cust_result else "N/A (Deleted)"
            cust_id_display = rent['CustomerID']
            
            start_date_display = format_date_display(rent.get('StartDate', 0)) 
            end_date_display = format_date_display(rent.get('EndDate', 0))
            
            car_status_text = "Rented" 
            rented_flag = "Yes"
            
        else:
            car_status_text = "Available"
        
        line_parts = [
            f"{car_data['ID']:<6}",
            f"{car_model:<20}",
            f"{car_plate:<12}", 
            f"{car_rate:,.2f}".ljust(10),
            f"{car_status_text:<10}",
            f"{rented_flag:<8}",
            f"{cust_id_display:<8}" if cust_id_display else f"{'':<8}",
            f"{cust_name:<30}" if cust_name else f"{'':<30}",
            f"{start_date_display:<10}" if start_date_display else f"{'':<10}",
            f"{end_date_display:<10}" if end_date_display else f"{'':<10}",
        ]

        report_content.append(' | '.join(line_parts))
    
    report_content.append("=" * 155)

=======
    model_count = defaultdict(int)
    for car in active_cars:
        brand = car['Model'].split(' ')[0] # ใช้คำแรกของ Model เป็น Brand
        model_count[brand] += 1 
        
    # 2. สร้างส่วนหัวรายงาน
    report_content = []
    report_content.append("Detailed Rental Summary Report")
    report_content.append(f"Generated At : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_content.append(f"Endianness   : Little-Endian")
    report_content.append(f"Time Zone    : +07:00 (Indochina Time)")
    report_content.append("-" * 120)
    
    # 3. ตารางรายละเอียดสัญญาเช่า (Active Rental Detail Table)
    
    fields = [
        ('Cust ID', 8), ('Name', 30), ('Car ID', 6), ('Model', 20),
        ('Start Date', 10), ('Return Date', 10), ('Car Status', 10), ('Rented', 8)
    ]
    
    header_line = ' | '.join(f"{name:<{length}}" for name, length in fields)
    report_content.append("ACTIVE RENTAL AGREEMENTS DETAIL:")
    report_content.append(header_line)
    report_content.append("-" * (sum(length for _, length in fields) + len(fields) * 3))

    if active_rentals:
        for rent in active_rentals:
            
            # ดึงข้อมูล Customer และ Car อย่างปลอดภัย (แก้ไขจุดที่อาจเกิดปัญหา Car ID)
            cust_name = cust_mgr.get_record_by_id(rent['CustomerID'])[0]['Name'] if cust_mgr.get_record_by_id(rent['CustomerID']) else "N/A (Deleted)"

            car_result = car_mgr.get_record_by_id(rent['CarID'])
            
            # 🟢 แก้ไขการดึงข้อมูลรถยนต์: ใช้ค่า Default เมื่อไม่พบ
            car_data = car_result[0] if car_result else {'Model': "N/A (Invalid)", 'IsActive': False}
            
            car_model = car_data['Model']
            car_is_active = car_data['IsActive']
            car_status_text = 'Active' if car_is_active else 'Inactive'
            
            # คำนวณวันที่ต้องคืน
            try:
                start_date_str = str(rent['StartDate']).zfill(8)
                start_date = datetime.datetime.strptime(start_date_str, '%d%m%Y')
                return_date = start_date + datetime.timedelta(days=rent['Days'])
                return_date_str = return_date.strftime('%d%m%Y')
            except ValueError:
                return_date_str = "Invalid"

            line_parts = [
                f"{rent['CustomerID']:<8}",
                f"{cust_name:<30}",
                f"{rent['CarID']:<6}",
                f"{car_model:<20}",
                f"{rent['StartDate']:<10}",
                f"{return_date_str:<10}",
                f"{car_status_text:<10}",
                f"{'Yes':<8}"
            ]

            report_content.append(' | '.join(line_parts))
    else:
        report_content.append("No active rental agreements found.")
        
    report_content.append("=" * 120)

    # 4. Summary และ Statistics
>>>>>>> 69bfc037f7880797c02da484f014d7fe289f2c67:PROJECT/CarManager.py
    report_content.append("\nSummary (ภาพรวมสถานะ Active)")
    report_content.append(f"- Total Cars (records) : {total_cars}")
    report_content.append(f"- Active Cars          : {len(active_cars)}")
    report_content.append(f"- Deleted Cars         : {deleted_cars}")
    report_content.append(f"- Currently Rented     : {currently_rented}")
    report_content.append(f"- Available Now        : {available_now}")
    
    report_content.append("\nRate Statistics (THB/day, Active only)")
    report_content.append(f"- Min : {min_rate:,.2f}")
    report_content.append(f"- Max : {max_rate:,.2f}")
    report_content.append(f"- Avg : {avg_rate:,.2f}")
    
<<<<<<< HEAD:PROJECT/Rental Program.py
    report_content.append("\nCars by Brand (Available Only)")
    if cars_by_brand:
        for brand, count in cars_by_brand.items():
            report_content.append(f"- {brand} : {count}")
    else:
        report_content.append("- None Available")
    
    report_content.append("\n" + "=" * 155)

=======
    report_content.append("\nCars by Model (Active only)")
    if model_count:
        for model, count in sorted(model_count.items()):
            report_content.append(f"- {model} : {count}")
    else:
        report_content.append("No active models found.")
    
    report_content.append("\n" + "=" * 120)
    
    # 5. เขียนไฟล์
>>>>>>> 69bfc037f7880797c02da484f014d7fe289f2c67:PROJECT/CarManager.py
    try:
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_content) + '\n')
        print(f"\n📄 รายงานสรุปละเอียดถูกสร้างสำเร็จที่ '{report_filename}'.")
    except IOError as e:
        print(f"❌ Error writing report file: {e}")

<<<<<<< HEAD:PROJECT/Rental Program.py
def format_date_display(date_int: int) -> str: 
    """Converts DDMMYYYY (int) to DD-MM-YYYY (str) for display."""
    date_str = str(date_int).zfill(8)
    if date_str == '00000000':
        return "N/A"

    try:
        date_obj = datetime.datetime.strptime(date_str, '%d%m%Y')
        return date_obj.strftime('%d-%m-%Y') 
    except ValueError:
        return "Invalid Date"
    
=======
>>>>>>> 69bfc037f7880797c02da484f014d7fe289f2c67:PROJECT/CarManager.py
# ==============================================================================
# 6. ฟังก์ชัน Main
# ==============================================================================

def main():
    print("🚀 เริ่มต้นระบบจัดการฐานข้อมูลเช่ารถยนต์...")
    car_mgr = CarManager()
    cust_mgr = CustomerManager()
    rental_mgr = RentalManager()

    try:
        while True:
            print("\n" + "="*50)
            print("             ระบบจัดการเช่ารถยนต์ (MAIN MENU)")
            print("="*50)
            print("[1] จัดการข้อมูลรถยนต์")
            print("[2] จัดการข้อมูลลูกค้า")
            print("[3] จัดการสัญญาเช่า")
<<<<<<< HEAD:PROJECT/Rental Program.py
            print("[R] สร้างรายงานรวมทั้งหมด (.txt)") 
=======
            print("[R] สร้างรายงานสรุปละเอียดทั้งหมด (.txt)") # 🟢 อัปเดตข้อความเมนู
>>>>>>> 69bfc037f7880797c02da484f014d7fe289f2c67:PROJECT/CarManager.py
            print("[X] ออกจากระบบ (ปิดไฟล์)")

            main_choice = get_user_choice(">> กรุณาเลือกเมนู: ", ['1', '2', '3', 'R', 'X']) 

            if main_choice == '1':
                run_car_menu(car_mgr)
            elif main_choice == '2':
                run_customer_menu(cust_mgr)
            elif main_choice == '3':
                run_rental_menu(rental_mgr, car_mgr, cust_mgr)
<<<<<<< HEAD:PROJECT/Rental Program.py
            elif main_choice == 'R':
                generate_detailed_summary_report(
                    car_mgr,
                    cust_mgr, 
                    rental_mgr,
                    report_filename='detailed_summary_report.txt'
                )
            elif main_choice == 'X':
                print("\n==============================================")
                print("  กำลังปิดระบบอย่างปลอดภัย...")
                print("==============================================")
                generate_detailed_summary_report(
                    car_mgr, 
                    cust_mgr, 
                    rental_mgr, 
                    report_filename='final_exit_summary.txt'
                )
                
                print("บันทึกและซิงค์ข้อมูล CarManager...")
                car_mgr.close() 
                print("บันทึกและซิงค์ข้อมูล CustomerManager...")
                cust_mgr.close()
                print("บันทึกและซิงค์ข้อมูล RentalManager...")
                rental_mgr.close()
                
                print("✅ ปิดโปรแกรมเรียบร้อยแล้ว")
                break 
                
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาดร้ายแรง: {e}")
=======
            
            # 📌 แก้ไขให้เรียกใช้ฟังก์ชันใหม่
            elif main_choice == 'R':
                generate_detailed_summary_report(
                    rental_mgr, 
                    cust_mgr, 
                    car_mgr, 
                    report_filename='detailed_summary_report.txt'
                )
            
            elif main_choice == 'X':
                print("\nปิดระบบและบันทึกข้อมูลทั้งหมด...")
                break
        
    except Exception as e:
        print(f"\n❌ เกิดข้อผิดพลาดร้ายแรง: {e}")
            
    finally:
        print("💾 กำลังปิดไฟล์ทั้งหมด...")
        car_mgr.close()
        cust_mgr.close()
        rental_mgr.close()
        print("✅ ปิดไฟล์ทั้งหมดเรียบร้อยแล้ว")
>>>>>>> 69bfc037f7880797c02da484f014d7fe289f2c67:PROJECT/CarManager.py

if __name__ == '__main__':
    main()