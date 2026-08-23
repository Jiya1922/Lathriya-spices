import io
import logging
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

logger = logging.getLogger(__name__)

def generate_payment_receipt(customer_name, payment_id, razorpay_order_id, items, total_amount, payment_date=None, payment_status="SUCCESS", customer_phone=None, customer_address=None):
    """
    Generates a clean, professional PDF payment receipt using ReportLab.
    Returns the binary content (bytes) of the generated PDF.
    
    Required Parameters:
    - customer_name: Full name of customer
    - payment_id: Razorpay Payment ID (e.g., pay_xxxxxxxxx)
    - razorpay_order_id: Razorpay Order ID or DB Order ID
    - items: List of dicts e.g. [{'product_name': 'Cardamom Powder (100g)', 'quantity': 2, 'price': 250.00}]
    - total_amount: Numeric price total e.g. 500.00
    - payment_date: Datetime object or formatted string
    - payment_status: Status string (default 'SUCCESS')
    - customer_phone: Phone number of customer (optional)
    - customer_address: Full delivery address of customer (optional)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette (Solid High-Contrast Black & Deep Forest Green)
    PRIMARY_COLOR = colors.HexColor('#1B5E20')  # Deep Forest Green
    GOLD_COLOR = colors.HexColor('#B8860B')     # Dark Metallic Gold
    DARK_TEXT = colors.HexColor('#000000')      # Pure Solid Black for maximum contrast
    LIGHT_BG = colors.HexColor('#f8fdf9')

    # Typography Styles (Dot Matrix / Monospace Digital Thermal Receipt Style - High Opacity Black)
    title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['Heading1'],
        fontName='Courier-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY_COLOR,
        alignment=0
    )

    subtitle_style = ParagraphStyle(
        'ReceiptSubtitle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#111111'),  # Crisp dark black
        alignment=0
    )

    label_style = ParagraphStyle(
        'FieldLabel',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=10,
        leading=14,
        textColor=DARK_TEXT
    )

    val_style = ParagraphStyle(
        'FieldValue',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=10,
        leading=14,
        textColor=DARK_TEXT
    )

    status_success_style = ParagraphStyle(
        'StatusSuccess',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=11,
        leading=14,
        textColor=PRIMARY_COLOR
    )

    story = []

    # 1. Header Section with Brand Logo & Farm Location
    import os
    from django.conf import settings
    from reportlab.platypus import Image as RLImage

    site_domain = getattr(settings, 'SITE_DOMAIN', '') or os.getenv('SITE_DOMAIN', 'lathriyaspices.com').strip()
    if not site_domain.startswith('www.') and not site_domain.startswith('http'):
        domain_url = f"www.{site_domain}"
    else:
        domain_url = site_domain

    if payment_date:
        if hasattr(payment_date, 'astimezone'):
            date_only_str = timezone.localtime(payment_date).strftime('%d %B %Y')
            formatted_date_str = timezone.localtime(payment_date).strftime('%d %B %Y, %I:%M %p IST')
        else:
            date_only_str = str(payment_date).split(' ')[0]
            formatted_date_str = str(payment_date)
    else:
        now_dt = timezone.localtime()
        date_only_str = now_dt.strftime('%d %B %Y')
        formatted_date_str = now_dt.strftime('%d %B %Y, %I:%M %p IST')

    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'main_logo.png')
    logo_img = None
    if os.path.exists(logo_path):
        try:
            logo_img = RLImage(logo_path, width=54, height=54)
        except Exception as img_err:
            logger.warning(f"Could not load logo in PDF: {img_err}")

    fssai_logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'home', 'fssai_logo.png')
    fssai_img = None
    if os.path.exists(fssai_logo_path):
        try:
            fssai_img = RLImage(fssai_logo_path, width=64, height=36)
        except Exception as fssai_err:
            logger.warning(f"Could not load FSSAI logo in PDF: {fssai_err}")

    # Clean up order reference display string
    raw_order_ref = str(razorpay_order_id or '').strip()
    if raw_order_ref.startswith('#'):
        order_ref_str = raw_order_ref
    elif raw_order_ref.isdigit():
        order_ref_str = f"#{raw_order_ref}"
    elif raw_order_ref.startswith('ORDER-'):
        order_ref_str = f"#{raw_order_ref}"
    else:
        order_ref_str = f"#{raw_order_ref}" if raw_order_ref else "N/A"

    if logo_img:
        header_data = [
            [
                logo_img,
                [
                    Paragraph("LATHRIYA SPICES", title_style),
                    Paragraph("Chottupara, K.P Colony, Idukki, Kerala, India<br/>FSSAI Lic. No: 21324123000456<br/>Email: lathriyaspices@gmail.com<br/>Phone: +91 90749 13271", subtitle_style)
                ],
                [
                    Paragraph("<b>PAYMENT RECEIPT</b>", ParagraphStyle('RightHeader', parent=styles['Normal'], fontName='Courier-Bold', fontSize=12, leading=16, textColor=GOLD_COLOR, alignment=2)),
                    Paragraph(f"Date: {formatted_date_str}", ParagraphStyle('RightDate', parent=styles['Normal'], fontName='Courier', fontSize=8.5, leading=11, textColor=colors.HexColor('#111111'), alignment=2))
                ]
            ]
        ]
        header_table = Table(header_data, colWidths=[60, 265, 195])
    else:
        header_data = [
            [
                Paragraph("LATHRIYA SPICES", title_style),
                Paragraph("<b>PAYMENT RECEIPT</b>", ParagraphStyle('RightHeader', parent=styles['Normal'], fontName='Courier-Bold', fontSize=12, leading=16, textColor=GOLD_COLOR, alignment=2))
            ],
            [
                Paragraph("Chottupara, K.P Colony, Idukki, Kerala, India<br/>FSSAI Lic. No: 21324123000456<br/>Email: lathriyaspices@gmail.com<br/>Phone: +91 90749 13271", subtitle_style),
                Paragraph(f"Date: {formatted_date_str}", ParagraphStyle('RightDate', parent=styles['Normal'], fontName='Courier', fontSize=8.5, leading=11, textColor=colors.HexColor('#111111'), alignment=2))
            ]
        ]
        header_table = Table(header_data, colWidths=[320, 200])

    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY_COLOR, spaceAfter=15))

    # 2. Payment & Customer Metadata Summary Grid (High Contrast Black & Full Client Details)
    formatted_status = str(payment_status).upper()
    meta_data = [
        [
            Paragraph("<b>Customer Name:</b>", label_style),
            Paragraph(str(customer_name or '').strip(), val_style),
        ]
    ]

    if customer_phone and str(customer_phone).strip():
        meta_data.append([
            Paragraph("<b>Phone Number:</b>", label_style),
            Paragraph(str(customer_phone).strip(), val_style),
        ])

    if customer_address and str(customer_address).strip():
        meta_data.append([
            Paragraph("<b>Delivery Address:</b>", label_style),
            Paragraph(str(customer_address).strip(), val_style),
        ])

    meta_data.extend([
        [
            Paragraph("<b>FSSAI License No:</b>", label_style),
            Paragraph("21324123000456", val_style),
        ],
        [
            Paragraph("<b>Razorpay Payment ID:</b>", label_style),
            Paragraph(f"<code>{payment_id or 'N/A'}</code>", val_style),
        ],
        [
            Paragraph("<b>Payment Status:</b>", label_style),
            Paragraph(f"<font color='#1B5E20'><b>{formatted_status}</b></font>", status_success_style)
        ],
        [
            Paragraph("<b>Payment Date:</b>", label_style),
            Paragraph(date_only_str, val_style)
        ]
    ])

    meta_table = Table(meta_data, colWidths=[140, 380])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e0e0e0')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#c8e6c9')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))

    # 3. Product Items Table
    story.append(Paragraph("<b>Order Items Breakdown</b>", ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontName='Courier-Bold', fontSize=13, leading=16, textColor=PRIMARY_COLOR)))
    story.append(Spacer(1, 8))

    item_rows = [
        [
            Paragraph("<b>Product Details</b>", label_style),
            Paragraph("<b>Qty</b>", ParagraphStyle('THC', parent=label_style, fontName='Courier-Bold', alignment=1)),
            Paragraph("<b>Unit Price</b>", ParagraphStyle('THC', parent=label_style, fontName='Courier-Bold', alignment=2)),
            Paragraph("<b>Total (INR)</b>", ParagraphStyle('THC', parent=label_style, fontName='Courier-Bold', alignment=2))
        ]
    ]

    if items:
        for itm in items:
            p_name = itm.get('product_name', 'Spice Product')
            p_qty = itm.get('quantity', 1)
            p_price = float(itm.get('price', 0))
            p_sub = p_qty * p_price

            item_rows.append([
                Paragraph(p_name, val_style),
                Paragraph(str(p_qty), ParagraphStyle('TC', parent=val_style, fontName='Courier', alignment=1)),
                Paragraph(f"Rs. {p_price:.2f}", ParagraphStyle('TR', parent=val_style, fontName='Courier', alignment=2)),
                Paragraph(f"Rs. {p_sub:.2f}", ParagraphStyle('TRb', parent=val_style, fontName='Courier-Bold', alignment=2))
            ])
    else:
        item_rows.append([
            Paragraph("Premium Spice Selection", val_style),
            Paragraph("1", ParagraphStyle('TC', parent=val_style, fontName='Courier', alignment=1)),
            Paragraph(f"Rs. {float(total_amount):.2f}", ParagraphStyle('TR', parent=val_style, fontName='Courier', alignment=2)),
            Paragraph(f"Rs. {float(total_amount):.2f}", ParagraphStyle('TRb', parent=val_style, fontName='Courier-Bold', alignment=2))
        ])

    # Total Row
    item_rows.append([
        Paragraph("<b>Grand Total Paid</b>", ParagraphStyle('GTL', parent=label_style, fontName='Courier-Bold', fontSize=11, textColor=PRIMARY_COLOR)),
        "", "",
        Paragraph(f"<b>Rs. {float(total_amount):.2f}</b>", ParagraphStyle('GTR', parent=label_style, fontName='Courier-Bold', fontSize=12, textColor=PRIMARY_COLOR, alignment=2))
    ])

    items_table = Table(item_rows, colWidths=[270, 50, 100, 100])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f5e9')),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor('#e0e0e0')),
        ('SPAN', (0,-1), (2,-1)),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#f0f7f1')),
        ('TOPPADDING', (0,-1), (-1,-1), 10),
        ('BOTTOMPADDING', (0,-1), (-1,-1), 10),
        ('LINEABOVE', (0,-1), (-1,-1), 1.5, PRIMARY_COLOR),
    ]))

    story.append(items_table)
    story.append(Spacer(1, 20))

    # 4. Premium Thank You Footer Card Box with FSSAI Logo
    thankyou_title_style = ParagraphStyle(
        'ThankYouTitle',
        parent=styles['Heading2'],
        fontName='Courier-Bold',
        fontSize=12,
        leading=15,
        textColor=PRIMARY_COLOR,
        alignment=1
    )

    thankyou_text_style = ParagraphStyle(
        'ThankYouText',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#444444'),
        alignment=1
    )

    thankyou_support_style = ParagraphStyle(
        'ThankYouSupport',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#666666'),
        alignment=1
    )

    if fssai_img:
        footer_content = [
            [fssai_img],
            [Paragraph("<b>FSSAI Registered Food Safety Guaranteed | Lic. No: 21324123000456</b>", ParagraphStyle('FSSAIHead', parent=styles['Normal'], fontName='Courier-Bold', fontSize=9, leading=12, textColor=PRIMARY_COLOR, alignment=1))],
            [Paragraph("Thank you for shopping with Lathriya Spices!", thankyou_title_style)],
            [Paragraph("This is an official digital payment receipt for your verified transaction.", thankyou_text_style)],
            [Paragraph(f"For any inquiries, please contact <b>lathriyaspices@gmail.com</b> or visit <b>{domain_url}</b>.", thankyou_support_style)]
        ]
    else:
        footer_content = [
            [Paragraph("<b>FSSAI Registered Food Safety Guaranteed | Lic. No: 21324123000456</b>", ParagraphStyle('FSSAIHead', parent=styles['Normal'], fontName='Courier-Bold', fontSize=9, leading=12, textColor=PRIMARY_COLOR, alignment=1))],
            [Paragraph("Thank you for shopping with Lathriya Spices!", thankyou_title_style)],
            [Paragraph("This is an official digital payment receipt for your verified transaction.", thankyou_text_style)],
            [Paragraph(f"For any inquiries, please contact <b>lathriyaspices@gmail.com</b> or visit <b>{domain_url}</b>.", thankyou_support_style)]
        ]

    footer_card_table = Table(footer_content, colWidths=[520])
    footer_card_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f7f1')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#c8e6c9')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    story.append(footer_card_table)

    # Build document
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    logger.info(f"Successfully generated PDF receipt for Payment ID {payment_id} ({len(pdf_bytes)} bytes)")
    return pdf_bytes
