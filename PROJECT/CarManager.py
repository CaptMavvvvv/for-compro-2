import struct
import os
import datetime
from typing import Dict, Any, List, Optional, Tuple

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

# Rental: < ?iiidid (IsActive, R_ID, C_ID, Car_ID, StartDate(int), Days, TotalPrice) -> 29 bytes
RENTAL_FORMAT = '< ?iiidid'
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
    
    # --- Utility Overrides (ต้องถูกกำหนดในคลาสลูก) ---

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
            
            # อ่านแค่ไบต์แรก (IsActive)
            status_byte = self.file.read(1)
            if not status_byte: break # ถึง EOF
            
            # อ่านไบต์ที่เหลือของระเบียน (เพื่อเลื่อนตัวชี้ไฟล์)
            remaining_bytes = self.file.read(self.record_size - 1)
            if len(remaining_bytes) < self.record_size - 1:
                # ถึง EOF ก่อนอ่านครบ (ข้อมูลอาจเสียหาย/ไม่สมบูรณ์)
                break
            
            # ตรวจสอบสถานะ
            is_active = struct.unpack('< ?', status_byte)[0]
            
            if not is_active:
                # พบช่องว่าง: นำมาใช้ใหม่ (Reuse Free Space)
                self.file.seek(current_offset, os.SEEK_SET) 
                self.file.write(packed_data)
                self.file.flush()
                print(f"✅ Reusing free space at offset: {current_offset} bytes in {self.filename}.")
                return current_offset
            
        # ถ้าไม่พบช่องว่าง: เพิ่มต่อท้าย (Append)
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
            # 💡 แก้ไข: ตรวจสอบว่าอ่านได้ครบขนาดระเบียนหรือไม่
            if len(record_bytes) < self.record_size: 
                break # ถึง EOF หรือข้อมูลไม่สมบูรณ์
            
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
            # 💡 แก้ไข: ตรวจสอบว่าอ่านได้ครบขนาดระเบียนหรือไม่
            if len(record_bytes) < self.record_size:
                break # ถึง EOF หรือข้อมูลไม่สมบูรณ์
            
            try:
                record_data = self._unpack_record(record_bytes)
                if record_data['IsActive']:
                    active_records.append(record_data)
            except struct.error: pass
        return active_records

    def generate_report(self, title: str, fields: List[Tuple[str, int]], report_filename: str):
        """สร้างไฟล์รายงานข้อความ (.txt) โดยอิงจากโครงสร้างข้อมูล"""
        self.file.seek(0, os.SEEK_SET)
        all_records = []
        while True:
            record_bytes = self.file.read(self.record_size)
            if len(record_bytes) < self.record_size: break # 💡 แก้ไข
            try:
                all_records.append(self._unpack_record(record_bytes))
            except struct.error: continue 
                
        total_records = len(all_records)
        active_count = sum(1 for r in all_records if r['IsActive'])
        deleted_count = total_records - active_count
        
        report_content = []
        report_content.append("=" * 60)
        report_content.append(f"{' ' * ((60 - len(title)) // 2)}{title}")
        report_content.append("=" * 60)
        report_content.append(f"Generated On: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_content.append(f"Binary File: {self.filename} | Size: {self.record_size} bytes")
        report_content.append("-" * 60)
        report_content.append("SUMMARY STATISTICS:")
        report_content.append(f"  - Total Records (In File): {total_records}")
        report_content.append(f"  - Active Records: {active_count}")
        report_content.append(f"  - Deleted/Free Space: {deleted_count}")
        report_content.append("-" * 60)
        report_content.append("ACTIVE RECORDS DETAIL:")

        header_line = ' | '.join(f"{name:<{length}}" for name, length in fields)
        report_content.append(header_line)
        report_content.append("-" * (sum(length for _, length in fields) + len(fields) * 3))

        if active_count > 0:
            for record in all_records:
                if record['IsActive']:
                    line_parts = []
                    for field_name, length in fields:
                        value = record.get(field_name, '')
                        if isinstance(value, float):
                            # แก้ไขการจัดรูปแบบ float
                            line_parts.append(f"{value:.2f}".ljust(length))
                        elif isinstance(value, int) and field_name in ('StartDate', 'ID', 'CustomerID', 'CarID'):
                             # แก้ไขการจัดรูปแบบ Int
                             line_parts.append(f"{value}".ljust(length)) 
                        else:
                            # 🟢 แก้ไขตรงนี้ 
                            line_parts.append(f"{str(value):<{length}}")
                    report_content.append(' | '.join(line_parts))
        else:
            report_content.append("No active records found.")
            
        report_content.append("=" * 60)
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_content) + '\n')
            print(f"📄 Report successfully generated to '{report_filename}'.")
        except IOError as e:
            print(f"❌ Error writing report file: {e}")


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
        # ตำแหน่งของ Model คือ 2, LicensePlate คือ 3, และ Rate คือ 4
        model = unpacked_data[2].split(b'\x00', 1)[0].decode(self.encoding, errors='ignore').strip()
        license_plate = unpacked_data[3].split(b'\x00', 1)[0].decode(self.encoding, errors='ignore').strip()
        
        return {
            'IsActive': unpacked_data[0], # <--- 🟢 ต้องมีคีย์นี้!
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
            data.get('IsActive', True),
            data['ID'],
            data['CustomerID'],
            data['CarID'],
            data['StartDate'],
            data['Days'],
            data['TotalPrice']
        )

    def _unpack_record(self, record_bytes: bytes) -> Dict[str, Any]:
        unpacked_data = struct.unpack(self.format, record_bytes)
        
        return {
            'IsActive': unpacked_data[0],
            'ID': unpacked_data[1],
            'CustomerID': unpacked_data[2],
            'CarID': unpacked_data[3],
            'StartDate': unpacked_data[4],
            'Days': unpacked_data[5],
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
    """รับอินพุตเป็นจำนวนเต็ม (ID, Days)"""
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

# ภายในส่วน Utility Functions
def get_date_input(prompt: str) -> int:
    """รับอินพุตวันที่และแปลงเป็น DDMMYYYY int"""
    while True:
        date_str = input(prompt + " (DDMMYYYY): ").strip() 
        if len(date_str) == 8 and date_str.isdigit():
            try:
                datetime.datetime.strptime(date_str, '%d%m%Y') 
                return int(date_str)
            except ValueError:
                print("❌ รูปแบบวันที่ไม่ถูกต้อง (ไม่ใช่ปี/เดือน/วันที่จริง)")
        else:
            print("❌ รูปแบบไม่ถูกต้อง กรุณาป้อนเป็น DDMMYYYY เช่น 25102025")

# ==============================================================================
# 5. ฟังก์ชันเมนูย่อยสำหรับแต่ละ Module
# ==============================================================================

def run_car_menu(manager: CarManager):
    while True:
        print("\n=== [1] จัดการข้อมูลรถยนต์ ===")
        print("A: เพิ่มรถยนต์ | U: แก้ไข | D: ลบ (Soft Delete)")
        print("V: ดูทั้งหมด | S: ค้นหาด้วย ID | R: สร้างรายงาน (.txt)")
        print("X: กลับสู่เมนูหลัก")
        
        choice = get_user_choice(">> กรุณาเลือก: ", ['A', 'U', 'D', 'V', 'S', 'R', 'X'])

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
                
        elif choice == 'R':
            manager.generate_report(
                "CAR RENTAL INVENTORY REPORT", 
                [('ID', 5), ('Model', 25), ('LicensePlate', 15), ('DailyRate', 12)], 
                'car_report.txt'
            )

        elif choice == 'X':
            break

def run_customer_menu(manager: CustomerManager):
    while True:
        print("\n=== [2] จัดการข้อมูลลูกค้า ===")
        print("A: เพิ่มลูกค้า | U: แก้ไข | D: ลบ (Soft Delete)")
        print("V: ดูทั้งหมด | S: ค้นหาด้วย ID | R: สร้างรายงาน (.txt)")
        print("X: กลับสู่เมนูหลัก")
        
        choice = get_user_choice(">> กรุณาเลือก: ", ['A', 'U', 'D', 'V', 'S', 'R', 'X'])
        
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

        elif choice == 'R':
            manager.generate_report(
                "CUSTOMER DIRECTORY REPORT", 
                [('ID', 5), ('Name', 30), ('Phone', 15)], 
                'customer_report.txt'
            )

        elif choice == 'X':
            break

def run_rental_menu(manager: RentalManager, car_mgr: CarManager, cust_mgr: CustomerManager):
    while True:
        print("\n=== [3] จัดการสัญญาเช่า ===")
        print("A: สร้างสัญญา | V: ดูทั้งหมด | S: ค้นหาด้วย ID")
        print("D: คืนรถ (Soft Delete) | R: สร้างรายงาน (.txt)")
        print("X: กลับสู่เมนูหลัก")
        
        choice = get_user_choice(">> กรุณาเลือก: ", ['A', 'V', 'D', 'S', 'R', 'X'])
        
        if choice == 'A':
            print("\n-- สร้างสัญญาเช่า --")
            rental_id = get_int_input("ID สัญญาเช่า: ")
            cust_id = get_int_input("ID ลูกค้า: ")
            car_id = get_int_input("ID รถยนต์: ")
            
            # ตรวจสอบ ID
            if not cust_mgr.get_record_by_id(cust_id):
                print("❌ ID ลูกค้าไม่ถูกต้อง หรือลูกค้าถูกลบไปแล้ว")
                continue
            car_result = car_mgr.get_record_by_id(car_id)
            if not car_result:
                print("❌ ID รถยนต์ไม่ถูกต้อง หรือรถถูกเช่าอยู่/ถูกลบไปแล้ว")
                continue
            
            car_data, _ = car_result
            daily_rate = car_data['DailyRate']
            
            start_date_int = get_date_input("วันที่เริ่มเช่า")
            days = get_int_input("จำนวนวันเช่า: ")
            total_price = daily_rate * days
            
            print(f"✅ คำนวณราคารวม: {daily_rate:.2f} * {days} วัน = {total_price:.2f} บาท")
            
            manager.add_record({
                'ID': rental_id, 'CustomerID': cust_id, 'CarID': car_id, 
                'StartDate': start_date_int, 'Days': days, 'TotalPrice': total_price
            })

        elif choice == 'V':
            print("\n-- รายการสัญญาเช่าทั้งหมด (Active) --")
            rentals = manager.get_all_records()
            if not rentals:
                print("ไม่มีสัญญาเช่าที่ใช้งานอยู่")
            else:
                for rent in rentals:
                    print(f"ID: {rent['ID']} | CustID: {rent['CustomerID']} | CarID: {rent['CarID']} | Start: {rent['StartDate']} | Days: {rent['Days']} | Total: {rent['TotalPrice']:.2f}")

        elif choice == 'D':
            print("\n-- คืนรถ (Soft Delete สัญญาเช่า) --")
            rental_id = get_int_input("ID สัญญาเช่าที่ต้องการปิด (คืนรถ): ")
            manager.delete_record(rental_id)

        elif choice == 'S':
            print("\n-- ค้นหาสัญญาเช่าด้วย ID --")
            rental_id = get_int_input("ID สัญญาเช่าที่ต้องการค้นหา: ")
            
            result = manager.get_record_by_id(rental_id)
            
            if result is not None:
                rent, offset = result
                print(f"✅ พบข้อมูล: ID: {rent['ID']} | CustID: {rent['CustomerID']} | CarID: {rent['CarID']} | Start: {rent['StartDate']} | Days: {rent['Days']} | Total: {rent['TotalPrice']:.2f} (Offset: {offset} bytes)")
            else:
                print("❌ ไม่พบสัญญาเช่า ID นี้ หรือสัญญานี้ถูกปิดไปแล้ว")

        elif choice == 'R':
            manager.generate_report(
                "RENTAL AGREEMENT SUMMARY", 
                [('ID', 5), ('CustomerID', 10), ('CarID', 7), ('StartDate', 10), ('Days', 5), ('TotalPrice', 12)], 
                'rental_report.txt'
            )

        elif choice == 'X':
            break

# ==============================================================================
# 6. ฟังก์ชัน Main
# ==============================================================================

def main():
    print("🚀 เริ่มต้นระบบจัดการฐานข้อมูลเช่ารถยนต์...")
    # 1. Initialize Managers
    car_mgr = CarManager()
    cust_mgr = CustomerManager()
    rental_mgr = RentalManager()

    try:
        while True:
            print("\n" + "="*50)
            print("          ระบบจัดการเช่ารถยนต์ (MAIN MENU)")
            print("="*50)
            print("[1] จัดการข้อมูลรถยนต์")
            print("[2] จัดการข้อมูลลูกค้า")
            print("[3] จัดการสัญญาเช่า")
            print("[X] ออกจากระบบ (ปิดไฟล์)")

            main_choice = get_user_choice(">> กรุณาเลือกเมนู: ", ['1', '2', '3', 'X'])

            if main_choice == '1':
                run_car_menu(car_mgr)
            elif main_choice == '2':
                run_customer_menu(cust_mgr)
            elif main_choice == '3':
                run_rental_menu(rental_mgr, car_mgr, cust_mgr)
            elif main_choice == 'X':
                print("\nปิดระบบและบันทึกข้อมูลทั้งหมด...")
                break
                
    except Exception as e:
        # ดักจับข้อผิดพลาดที่ไม่คาดคิดทั้งหมด
        print(f"\n❌ เกิดข้อผิดพลาด: {e}")
        
    finally:
        # 2. Close Files Safely (ส่วนนี้จะทำงานเสมอ ไม่ว่าจะเกิดข้อผิดพลาดหรือไม่)
        print("💾 กำลังปิดไฟล์ทั้งหมด...")
        car_mgr.close()
        cust_mgr.close()
        rental_mgr.close()
        print("✅ ปิดไฟล์ทั้งหมดเรียบร้อยแล้ว")

if __name__ == '__main__':
    main()