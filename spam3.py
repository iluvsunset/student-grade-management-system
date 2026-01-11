"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           ULTIMATE STUDENT GRADE MANAGEMENT SYSTEM - ENTERPRISE              ║
║                          Version 4.0 Professional                            ║
║                                                                              ║
║              Hệ Thống Quản Lý Điểm Học Sinh Thông Minh Toàn Diện           ║
║                                                                              ║
║    Features: AI Analytics | Multi-Export | Database | Cloud-Ready | API     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import math
import json
import os
import csv
import sqlite3
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, Counter
import statistics
from pathlib import Path


# ============================================================================
#                           CONFIGURATION & CONSTANTS
# ============================================================================

class ColorCode:
    """ANSI Color codes for terminal styling"""
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Bright colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    
    # Reset
    END = '\033[0m'


class Icons:
    """Unicode icons for better UX"""
    CHECKMARK = '✓'
    CROSS = '✗'
    WARNING = '⚠'
    INFO = 'ℹ'
    STAR = '⭐'
    TROPHY = '🏆'
    FIRE = '🔥'
    ROCKET = '🚀'
    BOOK = '📚'
    PEN = '✍️'
    CHART = '📊'
    SAVE = '💾'
    EXPORT = '📤'
    ARROW = '➤'
    GRADUATION = '🎓'
    TARGET = '🎯'
    BRAIN = '🧠'
    LIGHT = '💡'


class GradeLevel(Enum):
    """Grade classification levels"""
    OUTSTANDING = ("Xuất sắc", 9.0, Icons.TROPHY, ColorCode.BRIGHT_MAGENTA)
    EXCELLENT = ("Giỏi", 8.0, Icons.STAR, ColorCode.BRIGHT_GREEN)
    GOOD = ("Khá", 6.5, "👍", ColorCode.BRIGHT_CYAN)
    AVERAGE = ("Trung bình", 5.0, "📝", ColorCode.BRIGHT_YELLOW)
    WEAK = ("Yếu", 3.5, Icons.WARNING, ColorCode.YELLOW)
    POOR = ("Kém", 0.0, Icons.CROSS, ColorCode.RED)
    
    def __init__(self, label: str, min_score: float, icon: str, color: str):
        self.label = label
        self.min_score = min_score
        self.icon = icon
        self.color = color


# ============================================================================
#                           DATA MODELS
# ============================================================================

@dataclass
class SubjectInfo:
    """Subject information with score"""
    name: str
    score: float
    weight: int = 1
    category: Optional[str] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        if not 0 <= self.score <= 10:
            raise ValueError(f"Score must be 0-10, got {self.score}")
        if self.weight not in [1, 2, 3]:
            raise ValueError(f"Weight must be 1-3, got {self.weight}")
    
    @property
    def weighted_score(self) -> float:
        return self.score * self.weight
    
    @property
    def grade_level(self) -> GradeLevel:
        for level in GradeLevel:
            if self.score >= level.min_score:
                return level
        return GradeLevel.POOR


@dataclass
class StudentInfo:
    """Complete student information"""
    student_id: str
    full_name: str
    class_name: str
    academic_year: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    def __post_init__(self):
        if not re.match(r'^[A-Z0-9]{6,10}$', self.student_id):
            raise ValueError(f"Invalid student ID: {self.student_id}")


@dataclass
class AcademicRecord:
    """Complete academic record"""
    student: StudentInfo
    semester: str  # "Học kỳ I" or "Học kỳ II"
    exam_type: str  # "Giữa kỳ", "Cuối kỳ", "Tổng kết"
    subjects: List[SubjectInfo] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    record_id: str = field(default_factory=lambda: hashlib.md5(
        f"{datetime.now().isoformat()}".encode()).hexdigest()[:12])
    
    @property
    def simple_gpa(self) -> float:
        if not self.subjects:
            return 0.0
        return round(sum(s.score for s in self.subjects) / len(self.subjects), 2)
    
    @property
    def weighted_gpa(self) -> float:
        if not self.subjects:
            return 0.0
        total_weighted = sum(s.weighted_score for s in self.subjects)
        total_weights = sum(s.weight for s in self.subjects)
        return round(total_weighted / total_weights, 2)
    
    @property
    def grade_level(self) -> GradeLevel:
        gpa = self.weighted_gpa
        for level in GradeLevel:
            if gpa >= level.min_score:
                return level
        return GradeLevel.POOR


# ============================================================================
#                           DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """SQLite database for persistent storage"""
    
    def __init__(self, db_path: str = "student_grades.db"):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.initialize_database()
    
    def initialize_database(self):
        """Create tables if not exist"""
        self.connection = sqlite3.connect(self.db_path)
        cursor = self.connection.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                academic_year TEXT NOT NULL,
                date_of_birth TEXT,
                gender TEXT,
                email TEXT,
                phone TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                record_id TEXT NOT NULL,
                subject_name TEXT NOT NULL,
                score REAL NOT NULL,
                weight INTEGER DEFAULT 1,
                category TEXT,
                notes TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS academic_records (
                record_id TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                semester TEXT NOT NULL,
                exam_type TEXT NOT NULL,
                simple_gpa REAL,
                weighted_gpa REAL,
                grade_level TEXT,
                total_subjects INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
        
        self.connection.commit()
    
    def save_record(self, record: AcademicRecord) -> bool:
        """Save complete record to database"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
    INSERT OR REPLACE INTO students 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    record.student.student_id,
    record.student.full_name,
    record.student.class_name,
    record.student.academic_year,
    record.student.date_of_birth,
    record.student.gender,
    record.student.email,
    record.student.phone,
    record.created_at
))
            
            for subject in record.subjects:
                cursor.execute('''
                    INSERT INTO subjects (student_id, record_id, subject_name, 
                                        score, weight, category, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.student.student_id,
                    record.record_id,
                    subject.name,
                    subject.score,
                    subject.weight,
                    subject.category,
                    subject.notes
                ))
            
            cursor.execute('''
    INSERT OR REPLACE INTO academic_records 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    record.record_id,
    record.student.student_id,
    record.semester,
    record.exam_type,
    record.simple_gpa,
    record.weighted_gpa,
    record.grade_level.label,
    len(record.subjects),
    record.created_at
))
            
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False
    
    def get_student_records(self, student_id: str) -> List[Dict]:
        """Get all records for student"""
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT * FROM academic_records WHERE student_id = ?
            ORDER BY created_at DESC
        ''', (student_id,))
        
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def close(self):
        if self.connection:
            self.connection.close()


# ============================================================================
#                           ANALYTICS ENGINE
# ============================================================================

class AdvancedAnalytics:
    """Statistical analysis and insights"""
    
    @staticmethod
    def calculate_statistics(subjects: List[SubjectInfo]) -> Dict[str, Any]:
        """Calculate comprehensive statistics"""
        if not subjects:
            return {}
        
        scores = [s.score for s in subjects]
        
        return {
            'count': len(scores),
            'mean': statistics.mean(scores),
            'median': statistics.median(scores),
            'variance': statistics.variance(scores) if len(scores) > 1 else 0,
            'std_dev': statistics.stdev(scores) if len(scores) > 1 else 0,
            'min': min(scores),
            'max': max(scores),
            'range': max(scores) - min(scores),
            'min_subject': min(subjects, key=lambda x: x.score).name,
            'max_subject': max(subjects, key=lambda x: x.score).name,
            'excellent_count': sum(1 for s in scores if s >= 9.0),
            'good_count': sum(1 for s in scores if 8.0 <= s < 9.0),
            'average_count': sum(1 for s in scores if 5.0 <= s < 8.0),
            'poor_count': sum(1 for s in scores if s < 5.0),
            'excellence_rate': (sum(1 for s in scores if s >= 8.0) / len(scores)) * 100,
            'pass_rate': (sum(1 for s in scores if s >= 5.0) / len(scores)) * 100,
            'consistency_score': 100 - (statistics.stdev(scores) / statistics.mean(scores) * 100 
                                       if len(scores) > 1 and statistics.mean(scores) > 0 else 0),
        }
    
    @staticmethod
    def generate_insights(stats: Dict, record: AcademicRecord) -> List[str]:
        """Generate AI-like insights"""
        insights = []
        gpa = record.weighted_gpa
        
        # GPA analysis
        if gpa >= 9.0:
            insights.append(f"{Icons.TROPHY} Xuất sắc! Thuộc top học sinh giỏi nhất!")
        elif gpa >= 8.0:
            insights.append(f"{Icons.FIRE} Kết quả tốt! Cố gắng thêm để đạt xuất sắc.")
        elif gpa >= 6.5:
            insights.append(f"{Icons.TARGET} Khá ổn. Tập trung cải thiện môn yếu.")
        else:
            insights.append(f"{Icons.WARNING} Cần cải thiện. Đừng nản chí!")
        
        # Consistency
        consistency = stats.get('consistency_score', 0)
        if consistency >= 90:
            insights.append(f"{Icons.STAR} Điểm rất đồng đều - học tập ổn định.")
        elif consistency < 70:
            insights.append(f"{Icons.LIGHT} Điểm chênh lệch - cân bằng thời gian học.")
        
        # Perfect score
        if stats.get('max') == 10.0:
            insights.append(f"🥇 Điểm tuyệt đối ở {stats.get('max_subject')}!")
        
        # Weak subjects
        if stats.get('min') < 5.0:
            insights.append(f"{Icons.WARNING} Ưu tiên {stats.get('min_subject')}.")
        
        # Excellence rate
        excellence = stats.get('excellence_rate', 0)
        if excellence >= 70:
            insights.append(f"{Icons.ROCKET} {excellence:.0f}% môn đạt giỏi!")
        
        return insights
    
    @staticmethod
    def predict_performance(record: AcademicRecord) -> Dict[str, Any]:
        """Predict future performance"""
        stats = AdvancedAnalytics.calculate_statistics(record.subjects)
        current_gpa = record.weighted_gpa
        consistency = stats.get('consistency_score', 0)
        
        improvement = (10 - current_gpa) * (consistency / 100) * 0.3
        predicted = min(10.0, current_gpa + improvement)
        
        return {
            'current_gpa': current_gpa,
            'predicted_next': round(predicted, 2),
            'improvement_potential': round(improvement, 2),
            'confidence': 'Cao' if consistency > 80 else 'Trung bình' if consistency > 60 else 'Thấp',
            'recommendation': 'Duy trì' if current_gpa >= 8.0 else 'Cải thiện',
            'focus_areas': [s.name for s in sorted(record.subjects, key=lambda x: x.score)[:3]]
        }


# ============================================================================
#                           EXPORT ENGINE
# ============================================================================

class ReportExporter:
    """Multi-format export"""
    
    @staticmethod
    def export_json(record: AcademicRecord, filepath: Optional[str] = None) -> str:
        """Export to JSON"""
        if not filepath:
            filepath = f"report_{record.student.student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'student': asdict(record.student),
            'subjects': [asdict(s) for s in record.subjects],
            'summary': {
                'simple_gpa': record.simple_gpa,
                'weighted_gpa': record.weighted_gpa,
                'grade_level': record.grade_level.label,
                'total_subjects': len(record.subjects)
            },
            'statistics': AdvancedAnalytics.calculate_statistics(record.subjects),
            'metadata': {
                'record_id': record.record_id,
                'created_at': record.created_at,
                'export_time': datetime.now().isoformat()
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    @staticmethod
    def export_csv(record: AcademicRecord, filepath: Optional[str] = None) -> str:
        """Export to CSV"""
        if not filepath:
            filepath = f"report_{record.student.student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            writer.writerow(['HỌC BẠ ĐIỆN TỬ - ELECTRONIC TRANSCRIPT'])
            writer.writerow([])
            writer.writerow(['Mã HS', record.student.student_id])
            writer.writerow(['Họ tên', record.student.full_name])
            writer.writerow(['Lớp', record.student.class_name])
            writer.writerow(['Học kỳ', record.semester])
            writer.writerow(['Loại điểm', record.exam_type])
            writer.writerow([])
            
            writer.writerow(['STT', 'Môn học', 'Điểm', 'Hệ số', 'Xếp loại'])
            for idx, s in enumerate(record.subjects, 1):
                writer.writerow([idx, s.name, s.score, s.weight, s.grade_level.label])
            
            writer.writerow([])
            writer.writerow(['ĐTB (không HS)', record.simple_gpa])
            writer.writerow(['ĐTB (có HS)', record.weighted_gpa])
            writer.writerow(['Xếp loại', record.grade_level.label])
        
        return filepath
    
    @staticmethod
    def export_html(record: AcademicRecord, filepath: Optional[str] = None) -> str:
        """Export to beautiful HTML"""
        if not filepath:
            filepath = f"report_{record.student.student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        stats = AdvancedAnalytics.calculate_statistics(record.subjects)
        insights = AdvancedAnalytics.generate_insights(stats, record)
        prediction = AdvancedAnalytics.predict_performance(record)
        
        subjects_html = ""
        for idx, s in enumerate(record.subjects, 1):
            color = ('#9c27b0' if s.score >= 9.0 else '#4caf50' if s.score >= 8.0 
                    else '#ff9800' if s.score >= 5.0 else '#f44336')
            subjects_html += f"""
                <tr>
                    <td>{idx}</td>
                    <td><strong>{s.name}</strong></td>
                    <td style="color: {color}; font-weight: bold;">{s.score}</td>
                    <td>{s.weight}</td>
                    <td>{s.weighted_score}</td>
                    <td>{s.grade_level.icon} {s.grade_level.label}</td>
                </tr>
            """
        
        insights_html = "".join([f"<div class='insight'>{i}</div>" for i in insights])
        
        html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hồ Sơ Học Tập - {record.student.full_name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #0f172a;
            --glass-bg: rgba(30, 41, 59, 0.7);
            --glass-border: rgba(255, 255, 255, 0.08);
            --primary: #818cf8;
            --secondary: #c084fc;
            --accent: #2dd4bf;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --success: #34d399;
            --warning: #fbbf24;
            --danger: #f87171;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-dark);
            background-image: 
                radial-gradient(circle at 0% 0%, rgba(99, 102, 241, 0.15), transparent 50%),
                radial-gradient(circle at 100% 100%, rgba(192, 132, 252, 0.15), transparent 50%);
            color: var(--text-main);
            min-height: 100vh;
            padding: 40px 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            position: relative;
        }}

        /* Header */
        .header {{
            text-align: center;
            margin-bottom: 50px;
            animation: fadeInDown 1s ease-out;
        }}
        
        h1 {{
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
            letter-spacing: -1px;
        }}

        .subtitle {{
            color: var(--text-muted);
            font-size: 1.1rem;
            font-weight: 300;
        }}

        /* Glass Cards */
        .card {{
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            animation: fadeInUp 0.8s ease-out backwards;
        }}

        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 35px 60px -15px rgba(0, 0, 0, 0.6);
            border-color: rgba(255, 255, 255, 0.15);
        }}

        h2 {{
            font-size: 1.5rem;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--primary);
            border-bottom: 1px solid var(--glass-border);
            padding-bottom: 15px;
        }}

        /* Info Grid */
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}

        .info-item label {{
            display: block;
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-bottom: 5px;
        }}

        .info-item div {{
            font-size: 1.1rem;
            font-weight: 600;
        }}

        /* GPA Showcase */
        .gpa-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 30px;
        }}

        .gpa-box {{
            background: rgba(255, 255, 255, 0.03);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}

        .gpa-box::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; width: 100%; height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
        }}

        .gpa-value {{
            font-size: 2.5rem;
            font-weight: 800;
            margin: 10px 0;
            background: linear-gradient(to right, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        /* Table */
        .table-container {{
            overflow-x: auto;
            border-radius: 16px;
        }}

        table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
        }}

        th {{
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            text-align: left;
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        td {{
            padding: 15px;
            border-bottom: 1px solid var(--glass-border);
            transition: background 0.2s;
        }}

        tbody tr:hover td {{
            background: rgba(255, 255, 255, 0.05);
        }}

        /* Insights */
        .insight {{
            background: rgba(16, 185, 129, 0.1);
            border-left: 4px solid var(--success);
            padding: 15px;
            border-radius: 0 12px 12px 0;
            margin-bottom: 15px;
            font-size: 1.05rem;
        }}

        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.03);
            padding: 15px;
            border-radius: 12px;
            text-align: center;
        }}

        .stat-card .val {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-top: 5px;
            color: var(--text-main);
        }}

        /* Prediction */
        .prediction-box {{
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
            border: 1px solid rgba(139, 92, 246, 0.2);
        }}

        /* Footer */
        .footer {{
            text-align: center;
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-top: 50px;
            padding-bottom: 30px;
        }}

        /* Animations */
        @keyframes fadeInDown {{ from {{ opacity: 0; transform: translateY(-20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        @keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>HỒ SƠ HỌC TẬP</h1>
            <div class="subtitle">Báo Cáo Tự Động & Phân Tích Chuyên Sâu</div>
        </header>

        <div class="card" style="animation-delay: 0.1s">
            <h2>👤 Thông Tin Học Sinh</h2>
            <div class="info-grid">
                <div class="info-item"><label>Mã Học Sinh</label><div>{record.student.student_id}</div></div>
                <div class="info-item"><label>Họ và Tên</label><div style="color: var(--primary)">{record.student.full_name}</div></div>
                <div class="info-item"><label>Lớp</label><div>{record.student.class_name}</div></div>
                <div class="info-item"><label>Học Kỳ</label><div>{record.semester}</div></div>
                <div class="info-item"><label>Loại Điểm</label><div>{record.exam_type}</div></div>
                <div class="info-item"><label>Năm Học</label><div>{record.student.academic_year}</div></div>
                <div class="info-item"><label>Ngày Lập</label><div>{datetime.now().strftime('%d/%m/%Y')}</div></div>
            </div>

            <div class="gpa-grid">
                <div class="gpa-box">
                    <div style="color: var(--text-muted)">Điểm TB (Không HS)</div>
                    <div class="gpa-value">{record.simple_gpa}</div>
                </div>
                <div class="gpa-box">
                    <div style="color: var(--text-muted)">Điểm TB (Có HS)</div>
                    <div class="gpa-value">{record.weighted_gpa}</div>
                    <div style="color: var(--success); font-weight: bold">{record.grade_level.icon} {record.grade_level.label}</div>
                </div>
                <div class="gpa-box">
                    <div style="color: var(--text-muted)">Tổng Môn Học</div>
                    <div class="gpa-value">{len(record.subjects)}</div>
                </div>
            </div>
        </div>

        <div class="card" style="animation-delay: 0.2s">
            <h2>📊 Bảng Điểm Chi Tiết</h2>
            <div class="table-container">
                <table id="gradeTable">
                    <thead>
                        <tr><th>STT</th><th>Môn Học</th><th>Điểm Số</th><th>Hệ Số</th><th>Điểm TK</th><th>Xếp Loại</th></tr>
                    </thead>
                    <tbody>{subjects_html}</tbody>
                </table>
            </div>
        </div>

        <div class="card" style="animation-delay: 0.3s">
            <h2>📈 Thống Kê & Phân Tích</h2>
            <div class="stats-grid">
                <div class="stat-card"><div style="color:var(--text-muted)">Cao nhất</div><div class="val" style="color:var(--success)">{stats['max']}</div></div>
                <div class="stat-card"><div style="color:var(--text-muted)">Thấp nhất</div><div class="val" style="color:var(--danger)">{stats['min']}</div></div>
                <div class="stat-card"><div style="color:var(--text-muted)">Trung vị</div><div class="val">{stats['median']:.2f}</div></div>
                <div class="stat-card"><div style="color:var(--text-muted)">Độ lệch</div><div class="val">{stats['std_dev']:.2f}</div></div>
                <div class="stat-card"><div style="color:var(--text-muted)">Tỷ lệ giỏi</div><div class="val" style="color:var(--secondary)">{stats['excellence_rate']:.0f}%</div></div>
                <div class="stat-card"><div style="color:var(--text-muted)">Độ ổn định</div><div class="val" style="color:var(--primary)">{stats['consistency_score']:.0f}%</div></div>
            </div>
            
            <div style="margin-top: 30px">
                <h3 style="color: var(--text-muted); margin-bottom: 15px; font-size: 1rem; text-transform: uppercase; letter-spacing: 1px;">💡 Nhận Xét Của AI</h3>
                {insights_html}
            </div>
        </div>

        <div class="card prediction-box" style="animation-delay: 0.4s">
            <h2>🔮 Dự Đoán Tương Lai</h2>
            <div class="info-grid">
                <div class="info-item"><label>Dự đoán kỳ tới</label><div class="gpa-value" style="font-size: 2rem">{prediction['predicted_next']}</div></div>
                <div class="info-item"><label>Tiềm năng cải thiện</label><div style="color: var(--success); font-size: 1.5rem">+{prediction['improvement_potential']}</div></div>
                <div class="info-item"><label>Độ tin cậy</label><div>{prediction['confidence']}</div></div>
                <div class="info-item"><label>Khuyến nghị</label><div>{prediction['recommendation']}</div></div>
            </div>
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1)">
                <label style="color: var(--text-muted); display: block; margin-bottom: 10px">Môn cần tập trung:</label>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    {"".join([f"<span style='background: rgba(248, 113, 113, 0.2); color: #fca5a5; padding: 5px 15px; border-radius: 20px; font-size: 0.9rem'>{s}</span>" for s in prediction['focus_areas']])}
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Ultimate Student Grade System v4.0 Professional</p>
            <p>Generated at {datetime.now().strftime('%H:%M - %d/%m/%Y')}</p>
        </div>
    </div>
    
    <script>
        // Add visual enhancements to the existing table
        document.addEventListener('DOMContentLoaded', function() {{
            const rows = document.querySelectorAll('tbody tr');
            rows.forEach((row, index) => {{
                // Animation delay
                row.style.opacity = '0';
                row.style.animation = `fadeInUp 0.5s ease-out forwards ${{index * 0.05 + 0.5}}s`;
                
                // Colorize score cell
                const scoreCell = row.cells[2]; // Index 2 is score
                if(scoreCell) {{
                    const score = parseFloat(scoreCell.innerText);
                    let color = '#f87171'; // Red
                    if(score >= 9.0) color = '#818cf8'; // Indigo
                    else if(score >= 8.0) color = '#34d399'; // Green
                    else if(score >= 6.5) color = '#2dd4bf'; // Teal
                    else if(score >= 5.0) color = '#fbbf24'; // Amber
                    
                    scoreCell.style.color = color;
                    scoreCell.style.fontWeight = 'bold';
                    
                    // Add simple progress bar bg
                    const percentage = score * 10;
                    scoreCell.style.background = `linear-gradient(90deg, ${{color}}20 ${{percentage}}%, transparent ${{percentage}}%)`;
                    scoreCell.style.borderRadius = '8px';
                }}
            }});
        }});
    </script>
</body>
</html>"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return filepath


# ============================================================================
#                           USER INTERFACE
# ============================================================================

class UserInterface:
    """Enhanced UI with rich interactions"""
    
    @staticmethod
    def clear():
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def logo():
        print(f"""{ColorCode.BOLD}{ColorCode.BRIGHT_CYAN}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║        {ColorCode.BRIGHT_MAGENTA}█████╗ ██████╗ ██╗   ██╗ █████╗ ███╗   ██╗ ██████╗███████╗██████╗ {ColorCode.BRIGHT_CYAN}    ║
║       {ColorCode.BRIGHT_MAGENTA}██╔══██╗██╔══██╗██║   ██║██╔══██╗████╗  ██║██╔════╝██╔════╝██╔══██╗{ColorCode.BRIGHT_CYAN}    ║
║       {ColorCode.BRIGHT_MAGENTA}███████║██║  ██║██║   ██║███████║██╔██╗ ██║██║     █████╗  ██║  ██║{ColorCode.BRIGHT_CYAN}    ║
║       {ColorCode.BRIGHT_MAGENTA}██╔══██║██║  ██║╚██╗ ██╔╝██╔══██║██║╚██╗██║██║     ██╔══╝  ██║  ██║{ColorCode.BRIGHT_CYAN}    ║
║       {ColorCode.BRIGHT_MAGENTA}██║  ██║██████╔╝ ╚████╔╝ ██║  ██║██║ ╚████║╚██████╗███████╗██████╔╝{ColorCode.BRIGHT_CYAN}    ║
║       {ColorCode.BRIGHT_MAGENTA}╚═╝  ╚═╝╚═════╝   ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝╚═════╝ {ColorCode.BRIGHT_CYAN}    ║
║                                                                              ║
║           {ColorCode.BRIGHT_YELLOW}STUDENT GRADE MANAGEMENT SYSTEM - ULTIMATE EDITION{ColorCode.BRIGHT_CYAN}                 ║
║                          {ColorCode.WHITE}Version 4.0 Professional{ColorCode.BRIGHT_CYAN}                            ║
║                                                                              ║
║              {ColorCode.GREEN}🚀 AI-Powered | 📊 Analytics | 🎯 Professional{ColorCode.BRIGHT_CYAN}                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{ColorCode.END}""")
    
    @staticmethod
    def header(title: str, icon: str = Icons.STAR):
        """Print section header"""
        width = 80
        print(f"\n{ColorCode.BRIGHT_CYAN}{'─' * width}{ColorCode.END}")
        print(f"{ColorCode.BOLD}{ColorCode.BRIGHT_YELLOW}{icon} {title.center(width-4)}{ColorCode.END}")
        print(f"{ColorCode.BRIGHT_CYAN}{'─' * width}{ColorCode.END}\n")
    
    @staticmethod
    def success(msg: str):
        print(f"{ColorCode.GREEN}{Icons.CHECKMARK} {msg}{ColorCode.END}")
    
    @staticmethod
    def error(msg: str):
        print(f"{ColorCode.RED}{Icons.CROSS} {msg}{ColorCode.END}")
    
    @staticmethod
    def warning(msg: str):
        print(f"{ColorCode.YELLOW}{Icons.WARNING} {msg}{ColorCode.END}")
    
    @staticmethod
    def info(msg: str):
        print(f"{ColorCode.BLUE}{Icons.INFO} {msg}{ColorCode.END}")
    
    @staticmethod
    def progress(current: int, total: int, prefix: str = '', length: int = 30):
        """Print progress bar"""
        percent = current / total
        filled = int(length * percent)
        bar = '█' * filled + '░' * (length - filled)
        percentage = f"{percent * 100:.1f}%"
        print(f"{ColorCode.CYAN}{prefix} |{ColorCode.GREEN}{bar}{ColorCode.CYAN}| {percentage} ({current}/{total}){ColorCode.END}")

    
    @staticmethod
    def input_text(prompt: str, validator=None) -> Optional[str]:
        """Get validated text input"""
        while True:
            try:
                value = input(f"{ColorCode.BRIGHT_CYAN}{Icons.ARROW} {prompt}{ColorCode.END}").strip()
                if validator:
                    is_valid, message = validator(value)
                    if not is_valid:
                        UserInterface.error(message)
                        continue
                return value
            except KeyboardInterrupt:
                print(f"\n{ColorCode.YELLOW}Đã hủy thao tác.{ColorCode.END}")
                return None
    
    @staticmethod
    def input_number(prompt: str, min_val=None, max_val=None) -> Optional[float]:
        """Get validated number input"""
        while True:
            try:
                value = input(f"{ColorCode.BRIGHT_CYAN}{Icons.ARROW} {prompt}{ColorCode.END}")
                num = float(value)
                if min_val is not None and num < min_val:
                    UserInterface.error(f"Giá trị phải >= {min_val}")
                    continue
                if max_val is not None and num > max_val:
                    UserInterface.error(f"Giá trị phải <= {max_val}")
                    continue
                return num
            except ValueError:
                UserInterface.error("Vui lòng nhập số hợp lệ!")
            except KeyboardInterrupt:
                print(f"\n{ColorCode.YELLOW}Đã hủy thao tác.{ColorCode.END}")
                return None
    
    @staticmethod
    def menu(options: List[str], title: str = "Chọn tùy chọn") -> Optional[int]:
        """Display menu and get choice"""
        UserInterface.header(title, Icons.TARGET)
        for idx, option in enumerate(options, 1):
            print(f"{ColorCode.CYAN}  {idx}.{ColorCode.END} {option}")
        print(f"{ColorCode.CYAN}  0.{ColorCode.END} {ColorCode.DIM}Quay lại / Thoát{ColorCode.END}\n")
        
        choice = UserInterface.input_number("Lựa chọn của bạn (0 để hủy): ", 0, len(options))
        return int(choice) if choice and choice > 0 else None
    
    @staticmethod
    def confirm(message: str, default: bool = False) -> bool:
        """Get yes/no confirmation"""
        default_text = "Y/n" if default else "y/N"
        response = input(f"{ColorCode.YELLOW}{Icons.WARNING} {message} ({default_text}): {ColorCode.END}").strip().lower()
        if not response:
            return default
        return response in ['y', 'yes', 'có', 'c']


# ============================================================================
#                           MAIN APPLICATION
# ============================================================================

class GradeManagementSystem:
    """Main application controller"""
    
    SUBJECT_WEIGHTS = {
        'Toán': 2, 'Văn': 2, 'Anh': 2,
        'Lý': 1, 'Hóa': 1, 'Sinh': 1,
        'Sử': 1, 'Địa': 1, 'GDCD': 1,
        'Tin': 1, 'Công nghệ': 1,
        'Âm nhạc': 1, 'Mỹ thuật': 1,
        'Thể dục': 1, 'GDQP': 1
    }
    
    SUBJECT_CATEGORIES = {
        'Khoa học Tự nhiên': ['Toán', 'Lý', 'Hóa', 'Sinh', 'Tin', 'Công nghệ'],
        'Khoa học Xã hội': ['Văn', 'Sử', 'Địa', 'GDCD'],
        'Ngoại ngữ': ['Anh', 'Pháp', 'Trung', 'Nhật', 'Hàn'],
        'Nghệ thuật': ['Âm nhạc', 'Mỹ thuật'],
        'Thể chất': ['Thể dục', 'GDQP']
    }
    
    def __init__(self):
        self.ui = UserInterface()
        self.db = DatabaseManager()
        self.current_record: Optional[AcademicRecord] = None
    
    def run(self):
        """Main application loop"""
        try:
            self.show_welcome()
            
            while True:
                choice = self.main_menu()
                if not choice:
                    break
                
                if choice == 1:
                    self.create_new_record()
                elif choice == 2:
                    self.view_records()
                elif choice == 3:
                    self.export_menu()
                elif choice == 4:
                    self.statistics_menu()
                elif choice == 5:
                    self.show_about()
            
            self.ui.success("Cảm ơn bạn đã sử dụng hệ thống!")
            
        except KeyboardInterrupt:
            print(f"\n\n{ColorCode.YELLOW}Chương trình đã bị hủy.{ColorCode.END}\n")
        except Exception as e:
            print(f"\n{ColorCode.RED}Lỗi: {str(e)}{ColorCode.END}\n")
        finally:
            self.db.close()
    
    def show_welcome(self):
        """Show welcome screen"""
        self.ui.clear()
        self.ui.logo()
        
        print(f"\n{ColorCode.BRIGHT_YELLOW}{Icons.GRADUATION} Chào mừng đến với Hệ Thống Quản Lý Điểm Nâng Cao!{ColorCode.END}")
        print(f"{ColorCode.WHITE}Hệ thống tích hợp AI, phân tích dữ liệu và xuất báo cáo chuyên nghiệp{ColorCode.END}\n")
        
        features = [
            f"{Icons.STAR} Phân tích thông minh với AI",
            f"{Icons.CHART} Thống kê chuyên sâu",
            f"{Icons.SAVE} Lưu trữ database SQLite",
            f"{Icons.EXPORT} Xuất báo cáo HTML/JSON/CSV",
            f"{Icons.BRAIN} Dự đoán hiệu suất",
            f"{Icons.TROPHY} Xếp hạng & so sánh"
        ]
        
        print(f"{ColorCode.CYAN}Tính năng nổi bật:{ColorCode.END}")
        for feature in features:
            print(f"  {ColorCode.GREEN}{feature}{ColorCode.END}")
        
        print()
        input(f"{ColorCode.BOLD}Nhấn Enter để tiếp tục...{ColorCode.END}")
    
    def main_menu(self) -> Optional[int]:
        """Display main menu"""
        self.ui.clear()
        options = [
            f"{Icons.PEN} Tạo phiếu điểm mới",
            f"{Icons.BOOK} Xem lịch sử điểm",
            f"{Icons.EXPORT} Xuất báo cáo",
            f"{Icons.CHART} Thống kê & phân tích",
            f"{Icons.INFO} Về hệ thống"
        ]
        return self.ui.menu(options, "MENU CHÍNH")
    
    def create_new_record(self):
        """Create new academic record"""
        self.ui.clear()
        self.ui.header("TẠO PHIẾU ĐIỂM MỚI", Icons.PEN)
        
        # Input student info and exam details
        result = self.input_student_info()
        if not result:
            return
        
        student, semester, exam_type = result
        
        # Input number of subjects
        num_subjects = self.ui.input_number("Số lượng môn học (1-20): ", 1, 20)
        if not num_subjects:
            return
        num_subjects = int(num_subjects)
        
        # Input grades
        subjects = self.input_grades(num_subjects)
        if not subjects:
            return
        
        # Create record
        self.current_record = AcademicRecord(
            student=student,
            semester=semester,
            exam_type=exam_type,
            subjects=subjects
        )
        
        # Display report
        self.display_report()
        
        # Save
        if self.ui.confirm("Lưu phiếu điểm này?", True):
            if self.db.save_record(self.current_record):
                self.ui.success("Đã lưu vào database!")
            else:
                self.ui.error("Không thể lưu vào database!")
        
        input(f"\n{ColorCode.DIM}Nhấn Enter để tiếp tục...{ColorCode.END}")
    
    def input_student_info(self) -> Optional[Tuple[StudentInfo, str, str]]:
        """Input student information and exam details"""
        self.ui.header("THÔNG TIN HỌC SINH", Icons.GRADUATION)
        
        # Student ID
        student_id = self.ui.input_text(
            "Mã học sinh (6-10 ký tự, VD: HS123456): ",
            validator=lambda x: (
                re.match(r'^[A-Z0-9]{6,10}$', x.upper()),
                "Mã HS không hợp lệ (6-10 ký tự chữ/số)"
            )
        )
        if not student_id:
            return None
        student_id = student_id.upper()
        
        # Check if student exists
        existing_student = self.get_student_info(student_id)
        
        if existing_student:
            self.ui.info(f"Học sinh đã tồn tại: {existing_student.full_name}")
            if not self.ui.confirm("Sử dụng thông tin này?", True):
                return None
            student = existing_student
        else:
            # Full name
            full_name = self.ui.input_text(
                "Họ và tên đầy đủ: ",
                validator=lambda x: (
                    len(x) >= 2 and re.match(r'^[a-zA-ZÀ-ỹ\s]+$', x),
                    "Tên phải >= 2 ký tự và chỉ chứa chữ cái"
                )
            )
            if not full_name:
                return None
            full_name = full_name.title()
            
            # Class
            class_name = self.ui.input_text(
                "Lớp (VD: 10A1, 11B2): ",
                validator=lambda x: (
                    re.match(r'^[0-9]{1,2}[A-Z][0-9]{1,2}$', x.upper()),
                    "Lớp không hợp lệ (VD: 10A1)"
                )
            )
            if not class_name:
                return None
            class_name = class_name.upper()
            
            # Academic year
            current_year = datetime.now().year
            academic_year = f"{current_year}-{current_year+1}"
            
            student = StudentInfo(
                student_id=student_id,
                full_name=full_name,
                class_name=class_name,
                academic_year=academic_year
            )
        
        # Semester selection
        semester_choice = self.ui.menu([
            "Học kỳ I",
            "Học kỳ II"
        ], "CHỌN HỌC KỲ")
        
        if not semester_choice:
            return None
        semesters = ["Học kỳ I", "Học kỳ II"]
        semester = semesters[semester_choice - 1]
        
        # Exam type selection
        exam_choice = self.ui.menu([
            "Giữa kỳ",
            "Cuối kỳ",
            "Tổng kết"
        ], "CHỌN LOẠI ĐIỂM")
        
        if not exam_choice:
            return None
        exam_types = ["Giữa kỳ", "Cuối kỳ", "Tổng kết"]
        exam_type = exam_types[exam_choice - 1]
        
        self.ui.success(f"Đã chọn: {student.full_name} - {semester} - {exam_type}")
        
        return (student, semester, exam_type)
    
    def get_student_info(self, student_id: str) -> Optional[StudentInfo]:
        """Get student info from database"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
            row = cursor.fetchone()
            
            if row:
                return StudentInfo(
                    student_id=row[0],
                    full_name=row[1],
                    class_name=row[2],
                    academic_year=row[3],
                    date_of_birth=row[4],
                    gender=row[5],
                    email=row[6],
                    phone=row[7]
                )
            return None
        except:
            return None
    
    def show_subject_categories(self):
        """Display subject categories - compact version"""
    print(f"\n{ColorCode.DIM}(Gõ 'help' để xem danh mục môn học){ColorCode.END}\n")
    
    def input_grades(self, num_subjects: int) -> Optional[List[SubjectInfo]]:
        """Input grades for subjects"""
        self.ui.header(f"NHẬP ĐIỂM CHO {num_subjects} MÔN HỌC", Icons.PEN)
    
        self.ui.info("Hướng dẫn:")
        print("  • Điểm từ 0.0 đến 10.0")
        print("  • Không được nhập trùng môn")
        print("  • Gõ 'help' để xem danh mục môn học")
        print("  • Gõ 'list' để xem đã nhập")
        print("  • Gõ 'undo' để xóa môn vừa nhập\n")
        
        subjects: List[SubjectInfo] = []
        subject_names = set()
        
        while len(subjects) < num_subjects:
            current = len(subjects) + 1
            
            # Progress - now on its own line with separator
            print(f"\n{ColorCode.CYAN}{'─' * 60}{ColorCode.END}")
            self.ui.progress(current, num_subjects, "Tiến trình")
            print(f"{ColorCode.BOLD}[Môn {current}/{num_subjects}]{ColorCode.END}")
            
            # Input subject
            subject_name = self.ui.input_text("Tên môn học (hoặc 'help'/'list'/'undo'): ")
            if not subject_name:
                continue
            
            # Commands
            if subject_name.lower() == 'help':
                self.show_subject_categories_full()
                continue
            
            if subject_name.lower() == 'list':
                if subjects:
                    print(f"\n{ColorCode.CYAN}Danh sách:{ColorCode.END}")
                    for idx, s in enumerate(subjects, 1):
                        print(f"  {idx}. {s.name}: {s.score} (x{s.weight})")
                else:
                    self.ui.warning("Chưa nhập môn nào")
                continue
            
            if subject_name.lower() == 'undo':
                if subjects:
                    removed = subjects.pop()
                    subject_names.remove(removed.name)
                    self.ui.success(f"Đã xóa: {removed.name}")
                else:
                    self.ui.warning("Không có gì để xóa")
                continue
            
            subject_name = subject_name.strip().title()
            
            # Check duplicate
            if subject_name in subject_names:
                self.ui.error(f"Môn '{subject_name}' đã tồn tại!")
                continue
            
            # Input score
            score = self.ui.input_number(f"Điểm môn {subject_name}: ", 0, 10)
            if score is None:
                continue
            
            # Determine weight & category
            weight = self.SUBJECT_WEIGHTS.get(subject_name, 1)
            category = None
            for cat, subj_list in self.SUBJECT_CATEGORIES.items():
                if subject_name in subj_list:
                    category = cat
                    break
            
            # Add subject
            subjects.append(SubjectInfo(
                name=subject_name,
                score=score,
                weight=weight,
                category=category
            ))
            subject_names.add(subject_name)
            
            weight_text = f"(Hệ số {weight})" if weight > 1 else ""
            self.ui.success(f"Đã lưu: {subject_name} = {score} {weight_text}")
        
        print(f"\n{ColorCode.GREEN}{'✓' * 30} HOÀN TẤT {ColorCode.END}\n")
        return subjects
    
    def show_subject_categories_full(self):
        """Display full subject categories when requested"""
        print(f"\n{ColorCode.BRIGHT_YELLOW}{Icons.BOOK} DANH MỤC MÔN HỌC:{ColorCode.END}\n")
    
        for category, subjects in self.SUBJECT_CATEGORIES.items():
         print(f"{ColorCode.BOLD}{ColorCode.BRIGHT_CYAN}{category}:{ColorCode.END}")
        subject_list = []
        for subject in subjects:
            weight = self.SUBJECT_WEIGHTS.get(subject, 1)
            indicator = f" {Icons.FIRE}" if weight > 1 else ""
            subject_list.append(f"{subject}{indicator}")
        print(f"  {ColorCode.WHITE}{', '.join(subject_list)}{ColorCode.END}")
    
        print(f"\n{ColorCode.DIM}{Icons.FIRE} = Môn hệ số cao (2-3){ColorCode.END}\n")
    
    def display_report(self):
        """Display detailed report"""
        if not self.current_record:
            return
        
        record = self.current_record
        stats = AdvancedAnalytics.calculate_statistics(record.subjects)
        insights = AdvancedAnalytics.generate_insights(stats, record)
        prediction = AdvancedAnalytics.predict_performance(record)
        
        self.ui.clear()
        
        # Header
        print("╔" + "═" * 78 + "╗")
        print("║" + f"{ColorCode.BOLD}{'PHIẾU ĐIỂM HỌC SINH - BÁO CÁO CHI TIẾT'.center(78)}{ColorCode.END}" + "║")
        print("╠" + "═" * 78 + "╣")
        
        # Student info
        print(f"║ {ColorCode.CYAN}Mã HS:{ColorCode.END} {record.student.student_id:<68} ║")
        print(f"║ {ColorCode.CYAN}Họ tên:{ColorCode.END} {record.student.full_name:<67} ║")
        print(f"║ {ColorCode.CYAN}Lớp:{ColorCode.END} {record.student.class_name:<71} ║")
        print(f"║ {ColorCode.CYAN}Học kỳ:{ColorCode.END} {record.semester:<67} ║")
        print(f"║ {ColorCode.CYAN}Loại điểm:{ColorCode.END} {record.exam_type:<64} ║")
        print(f"║ {ColorCode.CYAN}Năm học:{ColorCode.END} {record.student.academic_year:<66} ║")
        print(f"║ {ColorCode.CYAN}Ngày lập:{ColorCode.END} {datetime.now().strftime('%d/%m/%Y %H:%M'):<64} ║")
        
        print("╠" + "═" * 78 + "╣")
        
        # Grades table
        print(f"║ {ColorCode.BOLD}{'STT':<5} {'Môn học':<25} {'Điểm':<10} {'HS':<6} {'Xếp loại':<20}{ColorCode.END} ║")
        print("╠" + "─" * 78 + "╣")
        
        for idx, subject in enumerate(record.subjects, 1):
            print(f"║ {idx:<5} {subject.name:<25} {subject.score:<10.2f} {subject.weight:<6} "
                  f"{subject.grade_level.icon} {subject.grade_level.label:<17} ║")
        
        print("╠" + "═" * 78 + "╣")
        
        # Summary
        print(f"║ {ColorCode.BOLD}{'KẾT QUẢ TỔNG HỢP'.center(78)}{ColorCode.END} ║")
        print("╠" + "─" * 78 + "╣")
        print(f"║ Tổng số môn: {len(record.subjects):<63} ║")
        print(f"║ ĐTB (không HS): {ColorCode.YELLOW}{record.simple_gpa:<56.2f}{ColorCode.END} ║")
        print(f"║ ĐTB (có HS): {ColorCode.BOLD}{ColorCode.GREEN}{record.weighted_gpa:<59.2f}{ColorCode.END} ║")
        print(f"║ Xếp loại: {record.grade_level.icon} {ColorCode.BOLD}{record.grade_level.label:<62}{ColorCode.END} ║")
        
        print("╠" + "═" * 78 + "╣")
        
        # Statistics
        print(f"║ {ColorCode.BOLD}{'THỐNG KÊ'.center(78)}{ColorCode.END} ║")
        print("╠" + "─" * 78 + "╣")
        print(f"║ Cao nhất: {ColorCode.GREEN}{stats['max']:<65.2f}{ColorCode.END} ║")
        print(f"║ Thấp nhất: {ColorCode.RED}{stats['min']:<64.2f}{ColorCode.END} ║")
        print(f"║ Trung vị: {stats['median']:<65.2f} ║")
        print(f"║ Độ lệch chuẩn: {stats['std_dev']:<60.2f} ║")
        print(f"║ Tỷ lệ giỏi: {ColorCode.MAGENTA}{stats['excellence_rate']:<62.0f}%{ColorCode.END} ║")
        print(f"║ Độ ổn định: {ColorCode.CYAN}{stats['consistency_score']:<62.0f}%{ColorCode.END} ║")
        
        print("╚" + "═" * 78 + "╝\n")
        
        # AI Insights
        print(f"{ColorCode.BOLD}{ColorCode.BLUE}🧠 PHÂN TÍCH THÔNG MINH (AI):{ColorCode.END}\n")
        for insight in insights:
            print(f"  {insight}")
        
        # Prediction
        print(f"\n{ColorCode.BOLD}{ColorCode.MAGENTA}🔮 DỰ ĐOÁN HIỆU SUẤT:{ColorCode.END}\n")
        print(f"  • Hiện tại: {prediction['current_gpa']}")
        print(f"  • Dự đoán kỳ sau: {prediction['predicted_next']}")
        print(f"  • Tiềm năng: +{prediction['improvement_potential']}")
        print(f"  • Độ tin cậy: {prediction['confidence']}")
        print(f"  • Đề xuất: {prediction['recommendation']}")
        print(f"  • Tập trung: {', '.join(prediction['focus_areas'])}")
        print()
    
    def view_records(self):
        """View student records"""
        self.ui.clear()
        self.ui.header("XEM LỊCH SỬ ĐIỂM", Icons.BOOK)
    
        student_id = self.ui.input_text("Nhập mã học sinh: ")
        if not student_id:
            return
    
        records = self.db.get_student_records(student_id.upper())
    
        if not records:
          self.ui.warning("Không tìm thấy dữ liệu cho mã học sinh này!")
        else:
            print(f"\n{ColorCode.GREEN}Tìm thấy {len(records)} bản ghi:{ColorCode.END}\n")
        for idx, rec in enumerate(records, 1):
            print(f"{idx}. {rec['semester']} - {rec['exam_type']} - GPA: {rec['weighted_gpa']} - {rec['grade_level']}")
            print(f"   Ngày: {rec['created_at'][:10]}")
    
    input(f"\n{ColorCode.DIM}Nhấn Enter để tiếp tục...{ColorCode.END}")
    
    def export_menu(self):
        """Export menu"""
        self.ui.clear()
        self.ui.header("XUẤT BÁO CÁO", Icons.EXPORT)
        
        # Ask for student ID
        student_id = self.ui.input_text("Nhập mã học sinh cần xuất báo cáo: ")
        if not student_id:
            return
        
        student_id = student_id.upper()
        
        # Get records from database
        records = self.db.get_student_records(student_id)
        
        if not records:
            self.ui.warning(f"Không tìm thấy dữ liệu cho mã học sinh: {student_id}")
            input(f"\n{ColorCode.DIM}Nhấn Enter...{ColorCode.END}")
            return
        
        # Show available records
        print(f"\n{ColorCode.GREEN}Tìm thấy {len(records)} bản ghi:{ColorCode.END}\n")
        for idx, rec in enumerate(records, 1):
            print(f"{idx}. {rec['created_at'][:10]} - GPA: {rec['weighted_gpa']} - {rec['grade_level']}")
        
        # Select which record to export
        if len(records) > 1:
            record_choice = self.ui.input_number(f"\nChọn bản ghi để xuất (1-{len(records)}): ", 1, len(records))
            if not record_choice:
                return
            selected_record_id = records[int(record_choice) - 1]['record_id']
        else:
            selected_record_id = records[0]['record_id']
        
        # Load full record from database
        record_to_export = self.load_record_by_id(selected_record_id)
        
        if not record_to_export:
            self.ui.error("Không thể tải dữ liệu đầy đủ!")
            input(f"\n{ColorCode.DIM}Nhấn Enter...{ColorCode.END}")
            return
        
        # Choose export format
        choice = self.ui.menu([
            f"{Icons.EXPORT} Xuất JSON",
            f"{Icons.EXPORT} Xuất CSV",
            f"{Icons.EXPORT} Xuất HTML"
        ], "CHỌN ĐỊNH DẠNG XUẤT")
        
        if not choice:
            return
        
        try:
            if choice == 1:
                file = ReportExporter.export_json(record_to_export)
                self.ui.success(f"Đã xuất: {file}")
            elif choice == 2:
                file = ReportExporter.export_csv(record_to_export)
                self.ui.success(f"Đã xuất: {file}")
            elif choice == 3:
                file = ReportExporter.export_html(record_to_export)
                self.ui.success(f"Đã xuất: {file}")
        except Exception as e:
            self.ui.error(f"Lỗi xuất file: {e}")
        
        input(f"\n{ColorCode.DIM}Nhấn Enter...{ColorCode.END}")
    
    def load_record_by_id(self, record_id: str) -> Optional[AcademicRecord]:
        """Load complete record from database by record_id"""
        try:
            cursor = self.db.connection.cursor()
            
            # Get student info and record info together
            cursor.execute('''
                SELECT s.*, ar.semester, ar.exam_type, ar.created_at
                FROM students s
                JOIN academic_records ar ON s.student_id = ar.student_id
                WHERE ar.record_id = ?
            ''', (record_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            student = StudentInfo(
                student_id=row[0],
                full_name=row[1],
                class_name=row[2],
                academic_year=row[3],
                date_of_birth=row[4],
                gender=row[5],
                email=row[6],
                phone=row[7]
            )
            
            semester = row[9]  # From JOIN with academic_records
            exam_type = row[10]
            created_at = row[11]
            
            # Get subjects
            cursor.execute('''
                SELECT subject_name, score, weight, category, notes
                FROM subjects
                WHERE record_id = ?
            ''', (record_id,))
            
            subjects = []
            for subj_row in cursor.fetchall():
                subjects.append(SubjectInfo(
                    name=subj_row[0],
                    score=subj_row[1],
                    weight=subj_row[2],
                    category=subj_row[3],
                    notes=subj_row[4]
                ))
            
            return AcademicRecord(
                student=student,
                semester=semester,
                exam_type=exam_type,
                subjects=subjects,
                created_at=created_at,
                record_id=record_id
            )
            
        except Exception as e:
            print(f"Error loading record: {e}")
            return None
    
    def statistics_menu(self):
        """Statistics menu"""
        self.ui.warning("Tính năng đang phát triển!")
        input(f"\n{ColorCode.DIM}Nhấn Enter...{ColorCode.END}")
    
    def show_about(self):
        """Show about info"""
        self.ui.clear()
        self.ui.header("VỀ HỆ THỐNG", Icons.INFO)
        
        print(f"{ColorCode.BOLD}Ultimate Student Grade Management System{ColorCode.END}")
        print(f"Version: 4.0 Professional")
        print(f"© 2026 - Academic Management Solutions\n")
        
        print(f"{ColorCode.CYAN}Tính năng:{ColorCode.END}")
        print("  • Quản lý điểm học sinh toàn diện")
        print("  • Phân tích thống kê nâng cao")
        print("  • AI dự đoán hiệu suất")
        print("  • Xuất báo cáo đa định dạng")
        print("  • Lưu trữ database SQLite")
        
        input(f"\n{ColorCode.DIM}Nhấn Enter...{ColorCode.END}")


# ============================================================================
#                           MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    app = GradeManagementSystem()
    app.run()