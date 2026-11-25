import csv
from io import BytesIO, StringIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.database.session import get_db
from app.models import Merchant, Transaction

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(current_user)])


def report_rows(db: Session, limit: int):
    rows = db.query(
        Merchant.code, Merchant.name, Merchant.category,
        func.count(Transaction.id).label("transactions"),
        func.coalesce(func.sum(Transaction.amount), 0).label("revenue"),
    ).join(Transaction, and_(Transaction.merchant_id == Merchant.id, Transaction.status == "successful"),
           isouter=True).group_by(Merchant.id, Merchant.code, Merchant.name, Merchant.category
           ).order_by(func.sum(Transaction.amount).desc()).limit(limit).all()
    return [
        {"merchant_code": row.code, "merchant_name": row.name, "category": row.category,
         "successful_transactions": int(row.transactions or 0), "revenue": float(row.revenue or 0)}
        for row in rows
    ]


@router.get("/merchants.csv")
def export_csv(limit: int = Query(1000, ge=1, le=10000), db: Session = Depends(get_db)):
    output = StringIO()
    rows = report_rows(db, limit)
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()) if rows else [
        "merchant_code", "merchant_name", "category", "successful_transactions", "revenue"
    ])
    writer.writeheader()
    writer.writerows(rows)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": 'attachment; filename="merchant-report.csv"'})


@router.get("/merchants.xlsx")
def export_excel(limit: int = Query(1000, ge=1, le=10000), db: Session = Depends(get_db)):
    from openpyxl import Workbook
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Merchant performance"
    rows = report_rows(db, limit)
    headers = list(rows[0].keys()) if rows else [
        "merchant_code", "merchant_name", "category", "successful_transactions", "revenue"
    ]
    sheet.append(headers)
    for row in rows:
        sheet.append([row[key] for key in headers])
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                             headers={"Content-Disposition": 'attachment; filename="merchant-report.xlsx"'})


@router.get("/merchants.pdf")
def export_pdf(limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
    rows = report_rows(db, limit)
    data = [["Code", "Merchant", "Category", "Transactions", "Revenue"]]
    data.extend([[r["merchant_code"], r["merchant_name"], r["category"],
                  r["successful_transactions"], f'{r["revenue"]:,.2f}'] for r in rows])
    stream = BytesIO()
    document = SimpleDocTemplate(stream, pagesize=landscape(letter), title="Merchant performance")
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FF0000")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#EAEAEA")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F8FA")]),
    ]))
    document.build([table])
    stream.seek(0)
    return StreamingResponse(stream, media_type="application/pdf",
                             headers={"Content-Disposition": 'attachment; filename="merchant-report.pdf"'})
