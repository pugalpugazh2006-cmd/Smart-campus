from models import db, User, FacultyProfile, StudentProfile, Attendance, Fee, Event, EventRegistration, Performance, Library, LibraryRecord, Transport, StudentTransport, QRSession, Syllabus, AdminProfile
from tinydb import Query, where

table_map = {
    'users': User,
    'faculty_profiles': FacultyProfile,
    'student_profiles': StudentProfile,
    'attendance': Attendance,
    'fees': Fee,
    'events': Event,
    'event_registrations': EventRegistration,
    'performance': Performance,
    'library': Library,
    'library_records': LibraryRecord,
    'transport': Transport,
    'student_transport': StudentTransport,
    'qr_sessions': QRSession,
    'syllabus': Syllabus,
    'admin_profiles': AdminProfile
}

class Document(dict):
    def __init__(self, value):
        super().__init__(value)
        self.doc_id = value.get('doc_id')

class MockTable:
    def __init__(self, model):
        self.model = model

    def __len__(self):
        return self.model.query.count()

    def __iter__(self):
        return iter(self.all())

    def all(self):
        records = self.model.query.all()
        return [Document(r.to_dict()) for r in records]

    def search(self, cond):
        records = self.all()
        return [r for r in records if cond(r)]

    def get(self, cond=None, doc_id=None):
        if doc_id is not None:
            obj = self.model.query.get(doc_id)
            return Document(obj.to_dict()) if obj else None
        if cond:
            for r in self.all():
                if cond(r):
                    return r
        return None

    def insert(self, data):
        obj = self.model(**data)
        db.session.add(obj)
        db.session.commit()
        return obj.id

    def update(self, data, doc_ids=None, cond=None):
        updated = False
        if doc_ids:
            for d_id in doc_ids:
                obj = self.model.query.get(d_id)
                if obj:
                    for k, v in data.items():
                        setattr(obj, k, v)
                    updated = True
        elif cond:
            for record in self.model.query.all():
                document = Document(record.to_dict())
                if cond(document):
                    for k, v in data.items():
                        setattr(record, k, v)
                    updated = True
        if updated:
            db.session.commit()
        return updated

    def upsert(self, data, cond):
        existing = self.get(cond=cond)
        if existing:
            self.update(data, doc_ids=[existing['doc_id']])
        else:
            self.insert(data)

    def remove(self, cond=None, doc_ids=None):
        removed = False
        if doc_ids:
            for d_id in doc_ids:
                obj = self.model.query.get(d_id)
                if obj:
                    db.session.delete(obj)
                    removed = True
        elif cond:
            for record in self.model.query.all():
                document = Document(record.to_dict())
                if cond(document):
                    db.session.delete(record)
                    removed = True
        if removed:
            db.session.commit()
        return removed

class MockDB:
    def table(self, table_name):
        model = table_map.get(table_name)
        if not model:
            raise ValueError(f"Table {table_name} not found in model mapping")
        return MockTable(model)

    def tables(self):
        return list(table_map.keys())
