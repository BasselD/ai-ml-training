import teradatasql
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from io import BytesIO

# Database Connection
def fetch_data_from_teradata(query):
    with teradatasql.connect(host='your_host', user='your_user', password='your_password') as conn:
        return pd.read_sql(query, conn)

# Generate In-Memory Chart Buffer
def generate_chart_image(data):
    fig, ax = plt.subplots(figsize=(6, 4))
    data.plot(kind='bar', ax=ax)
    buf = BytesIO()
    plt.savefig(buf, format='PNG')
    plt.close(fig)
    buf.seek(0)
    return buf

# KPI Dashboard Chart
def generate_kpi_dashboard(kpi_data):
    fig, ax = plt.subplots(figsize=(12, 3), dpi=200)
    for i, kpi in enumerate(kpi_data):
        rect = patches.FancyBboxPatch(
            xy=(0.06 + i * 0.25, 0.1),
            width=0.18,
            height=0.7,
            boxstyle=f'round,pad=0.01,rounding_size=0.01',
            ec='#cccbca',
            fc='white'
        )
        ax.add_patch(rect)
        ax.text(0.06 + i * 0.25, 0.7, kpi['label'], ha='left', va='center', fontsize=14, color='#999999')
        ax.text(0.15 + i * 0.25, 0.5, f"{kpi['value']}", ha='center', va='center', fontsize=36, color='#424242', weight='bold')
        if kpi['change'] > 0:
            ax.text(0.15 + i * 0.25, 0.35, f"↑ {kpi['change']}%", ha='left', va='center', fontsize=14, color=kpi['color'])
        else:
            ax.text(0.15 + i * 0.25, 0.35, f"↓ {abs(kpi['change'])}%", ha='left', va='center', fontsize=14, color=kpi['color'])
        ax.text(0.15 + i * 0.25, 0.2, f"Target: {kpi['target']:.0f}", ha='center', va='center', fontsize=12, color='gray')
    ax.axis('off')
    ax.set_title('KPI Dashboard', fontsize=20)
    buf = BytesIO()
    plt.savefig(buf, format='PNG')
    plt.close(fig)
    buf.seek(0)
    return buf

# Revenue vs Cost Chart
def generate_revenue_cost_chart(df):
    fig, ax = plt.subplots(figsize=(4, 7))
    for type_, color in [('Revenue', '#67E480'), ('Cost', '#F36781')]:
        mask = df['Type'] == type_
        ax.bar(df.loc[mask, 'Year'], df.loc[mask, 'Amount'], color=color, label=type_)
    for _, row in df.iterrows():
        ax.text(row['Year'], row['Amount'] + 2 * (row['Amount'] > 0), f'${abs(row["Amount"])} M', ha='center', va='bottom' if row['Amount'] > 0 else 'top', color=row['Color'], weight='semibold', size=12)
    for year in set(df['Year']):
        rev = df.loc[(df['Year'] == year) & (df['Type'] == 'Revenue'), 'Amount'].values[0]
        cost = df.loc[(df['Year'] == year) & (df['Type'] == 'Cost'), 'Amount'].values[0]
        profit = rev + cost
        ax.plot([year - 0.4, year + 0.4], [profit, profit], color='#37505C', linestyle=(0, (5, 2)), linewidth=1.5, label='Profit' if year == min(set(df['Year'])) else None)
        ax.text(year, profit, f'${profit} M', ha='center', va='bottom', color='#37505C', size=11, weight='bold')
        ax.text(year, 0, f'{year}', ha='center', va='center', color='white', size=18, weight='bold')
    ax.set_title('Revenue and Cost by Year', color='#464646', size=20)
    ax.set_xlabel('Year')
    ax.set_ylabel('Amount')
    ax.set_ylim(-200, 250)
    ax.axhline(0, color='gray')
    ax.legend(loc='upper center', ncol=3, labelcolor='#464646')
    ax.axis('off')
    buf = BytesIO()
    plt.savefig(buf, format='PNG')
    plt.close(fig)
    buf.seek(0)
    return buf

# Generate PDF Report
def generate_pdf(provider_name, data, chart_buf, output_filename):
    c = canvas.Canvas(output_filename, pagesize=letter)

    # Cover Page
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(300, 700, "PCP Financial Packets")
    c.setFont("Helvetica", 16)
    c.drawCentredString(300, 650, f"Provider: {provider_name}")
    c.showPage()

    c.drawString(100, 750, f'Report for {provider_name}')
    c.drawImage(chart_buf, 100, 500, width=400, height=200)

    table_data = [data.columns.tolist()] + data.values.tolist()
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    table.wrapOn(c, 400, 300)
    table.drawOn(c, 100, 300)

    c.showPage()
    c.save()

# Save Data to Excel
def save_to_excel(data, filename):
    data.to_excel(filename, index=False)

# Main Execution
def main():
    query = "SELECT provider_name, metric1, metric2 FROM healthcare_data"
    df = fetch_data_from_teradata(query)

    for provider in df['provider_name'].unique():
        provider_data = df[df['provider_name'] == provider]
        chart_buf = generate_chart_image(provider_data[['metric1', 'metric2']])
        pdf_file = f'report_{provider}.pdf'
        excel_file = 'healthcare_data.xlsx'

        generate_pdf(provider, provider_data, chart_buf, pdf_file)

    save_to_excel(df, excel_file)
    print("Reports and Excel file generated successfully!")

if __name__ == "__main__":
    main()
