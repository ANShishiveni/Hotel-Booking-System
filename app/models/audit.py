"""
AuditLog model for tracking all changes in the system
"""

from app import db
from datetime import datetime
import json
from sqlalchemy import event
from flask import request

class AuditLog(db.Model):
    """Audit log model for tracking all changes"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(20), nullable=False)  # INSERT, UPDATE, DELETE
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Index for better query performance
    __table_args__ = (
        db.Index('idx_audit_table_record', 'table_name', 'record_id'),
        db.Index('idx_audit_user', 'user_id'),
        db.Index('idx_audit_created', 'created_at'),
    )
    
    def __repr__(self):
        return f'<AuditLog {self.action} {self.table_name}:{self.record_id}>'
    
    @classmethod
    def log_creation(cls, table_name, record_id, new_values, user_id=None):
        """Log record creation"""
        audit_log = cls(
            table_name=table_name,
            record_id=record_id,
            action='INSERT',
            new_values=new_values,
            user_id=user_id,
            ip_address=cls._get_client_ip(),
            user_agent=cls._get_user_agent()
        )
        db.session.add(audit_log)
        db.session.commit()
    
    @classmethod
    def log_update(cls, table_name, record_id, new_values, user_id=None, old_values=None):
        """Log record update"""
        audit_log = cls(
            table_name=table_name,
            record_id=record_id,
            action='UPDATE',
            old_values=old_values,
            new_values=new_values,
            user_id=user_id,
            ip_address=cls._get_client_ip(),
            user_agent=cls._get_user_agent()
        )
        db.session.add(audit_log)
        db.session.commit()
    
    @classmethod
    def log_deletion(cls, table_name, record_id, old_values, user_id=None):
        """Log record deletion"""
        audit_log = cls(
            table_name=table_name,
            record_id=record_id,
            action='DELETE',
            old_values=old_values,
            user_id=user_id,
            ip_address=cls._get_client_ip(),
            user_agent=cls._get_user_agent()
        )
        db.session.add(audit_log)
        db.session.commit()
    
    @classmethod
    def log_custom_action(cls, table_name, record_id, action, details, user_id=None):
        """Log custom action"""
        audit_log = cls(
            table_name=table_name,
            record_id=record_id,
            action=action,
            new_values=details,
            user_id=user_id,
            ip_address=cls._get_client_ip(),
            user_agent=cls._get_user_agent()
        )
        db.session.add(audit_log)
        db.session.commit()
    
    @staticmethod
    def _get_client_ip():
        """Get client IP address"""
        try:
            if request:
                # Check for forwarded headers first
                forwarded_for = request.headers.get('X-Forwarded-For')
                if forwarded_for:
                    return forwarded_for.split(',')[0].strip()
                
                real_ip = request.headers.get('X-Real-IP')
                if real_ip:
                    return real_ip
                
                return request.remote_addr
        except RuntimeError:
            # Outside request context
            pass
        return None
    
    @staticmethod
    def _get_user_agent():
        """Get user agent string"""
        try:
            if request:
                return request.headers.get('User-Agent')
        except RuntimeError:
            # Outside request context
            pass
        return None
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'action': self.action,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_audit_trail(cls, table_name, record_id, limit=100):
        """Get audit trail for a specific record"""
        return cls.query.filter_by(
            table_name=table_name,
            record_id=record_id
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_user_activity(cls, user_id, limit=100):
        """Get audit trail for a specific user"""
        return cls.query.filter_by(
            user_id=user_id
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_recent_activity(cls, hours=24, limit=100):
        """Get recent activity"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return cls.query.filter(
            cls.created_at >= cutoff_time
        ).order_by(cls.created_at.desc()).limit(limit).all()
