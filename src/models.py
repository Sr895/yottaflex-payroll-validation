"""SQLAlchemy database entities for the payroll workflow."""
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text,
    UniqueConstraint, func
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"
    id = Column(String(30), primary_key=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, nullable=False)
    department = Column(String(80), nullable=False)
    pay_group_id = Column(String(30), ForeignKey("pay_groups.id"), nullable=False)
    active = Column(Boolean, default=True, nullable=False)

class PayGroup(Base):
    __tablename__ = "pay_groups"
    id = Column(String(30), primary_key=True)
    name = Column(String(80), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    standard_hours_per_period = Column(Numeric(10, 2), default=160, nullable=False)

class PayPeriod(Base):
    __tablename__ = "pay_periods"
    id = Column(String(30), primary_key=True)
    period_name = Column(String(20), unique=True, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), default="OPEN", nullable=False)

class TimeEntry(Base):
    __tablename__ = "time_entries"
    id = Column(String(40), primary_key=True)
    employee_id = Column(String(30), ForeignKey("employees.id"), nullable=False)
    pay_period_id = Column(String(30), ForeignKey("pay_periods.id"), nullable=False)
    work_date = Column(Date, nullable=False)
    hours = Column(Numeric(8, 2), nullable=False)
    approved = Column(Boolean, default=True, nullable=False)
    source_ref = Column(String(60), nullable=False)

class LeaveRecord(Base):
    __tablename__ = "leave_records"
    id = Column(String(40), primary_key=True)
    employee_id = Column(String(30), ForeignKey("employees.id"), nullable=False)
    pay_period_id = Column(String(30), ForeignKey("pay_periods.id"), nullable=False)
    leave_date = Column(Date, nullable=False)
    leave_type = Column(String(30), nullable=False)
    days = Column(Numeric(5, 2), nullable=False)
    approved = Column(Boolean, default=True, nullable=False)

class Allowance(Base):
    __tablename__ = "allowances"
    id = Column(String(40), primary_key=True)
    employee_id = Column(String(30), ForeignKey("employees.id"), nullable=False)
    pay_period_id = Column(String(30), ForeignKey("pay_periods.id"), nullable=False)
    allowance_type = Column(String(40), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    source_ref = Column(String(60), nullable=False)

class Deduction(Base):
    __tablename__ = "deductions"
    id = Column(String(40), primary_key=True)
    employee_id = Column(String(30), ForeignKey("employees.id"), nullable=False)
    pay_period_id = Column(String(30), ForeignKey("pay_periods.id"), nullable=False)
    deduction_type = Column(String(40), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    source_ref = Column(String(60), nullable=False)

class PayrollInput(Base):
    __tablename__ = "payroll_inputs"
    id = Column(String(50), primary_key=True)
    employee_id = Column(String(30), ForeignKey("employees.id"), nullable=False)
    pay_period_id = Column(String(30), ForeignKey("pay_periods.id"), nullable=False)
    regular_hours = Column(Numeric(10, 2), nullable=False)
    leave_days = Column(Numeric(8, 2), nullable=False)
    allowance_total = Column(Numeric(14, 2), nullable=False)
    deduction_total = Column(Numeric(14, 2), nullable=False)
    gross_pay = Column(Numeric(14, 2), nullable=False)
    net_pay = Column(Numeric(14, 2), nullable=False)
    status = Column(String(20), default="PENDING", nullable=False)
    __table_args__ = (UniqueConstraint("employee_id", "pay_period_id"),)

class ValidationRule(Base):
    __tablename__ = "validation_rules"
    id = Column(String(40), primary_key=True)
    rule_code = Column(String(60), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)

class ExceptionRecord(Base):
    __tablename__ = "exceptions"
    id = Column(String(50), primary_key=True)
    payroll_input_id = Column(String(50), ForeignKey("payroll_inputs.id"), nullable=True)
    source_record_id = Column(String(50), nullable=False)
    rule_code = Column(String(60), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="OPEN", nullable=False)

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(String(50), primary_key=True)
    payroll_input_id = Column(String(50), ForeignKey("payroll_inputs.id"), nullable=False)
    approver = Column(String(120), nullable=False)
    decision = Column(String(20), nullable=False)
    comments = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

class PayrollExport(Base):
    __tablename__ = "payroll_exports"
    id = Column(String(50), primary_key=True)
    pay_period_id = Column(String(30), ForeignKey("pay_periods.id"), nullable=False)
    file_name = Column(String(200), nullable=False)
    record_count = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
