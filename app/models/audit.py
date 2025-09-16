from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(50), nullable=False)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer)
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.table_name}>'
    
    @staticmethod
    def log_action(user_id, action, table_name, record_id=None, old_values=None, new_values=None, ip_address=None, user_agent=None):
        """Create audit log entry with safe serialization"""
        from app.core.security import SecurityManager
        
        # Safely serialize values to prevent unicode errors
        safe_old_values = None
        safe_new_values = None
        
        if old_values:
            try:
                # Ensure all values are safely converted to strings
                safe_old_values = {
                    key: SecurityManager.safe_str(value) for key, value in old_values.items()
                }
            except Exception as e:
                # Fallback: store error info
                safe_old_values = {'serialization_error': str(e)}
        
        if new_values:
            try:
                # Ensure all values are safely converted to strings
                safe_new_values = {
                    key: SecurityManager.safe_str(value) for key, value in new_values.items()
                }
            except Exception as e:
                # Fallback: store error info
                safe_new_values = {'serialization_error': str(e)}
        
        log = AuditLog(
            user_id=user_id,
            action=SecurityManager.safe_str(action),
            table_name=SecurityManager.safe_str(table_name),
            record_id=record_id,
            old_values=safe_old_values,
            new_values=safe_new_values,
            ip_address=SecurityManager.safe_str(ip_address) if ip_address else None,
            user_agent=SecurityManager.safe_str(user_agent) if user_agent else None
        )
        db.session.add(log)
        return log
    
    def to_dict(self):
        """Convert audit log to dictionary with safe string handling"""
        from app.core.security import SecurityManager
        
        return {
            'id': self.id,
            'user': SecurityManager.safe_str(self.user.username) if self.user else 'System',
            'action': SecurityManager.safe_str(self.action),
            'table_name': SecurityManager.safe_str(self.table_name),
            'record_id': self.record_id,
            'ip_address': SecurityManager.safe_str(self.ip_address),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }