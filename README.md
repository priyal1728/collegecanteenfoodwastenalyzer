# College Canteen Food Waste Analyzer

A Big Data and Hadoop-inspired analytics project for tracking and reducing food waste in a college canteen. The project combines a real-world dataset, Apache Spark-based data processing, and a modern Streamlit dashboard to uncover waste patterns and support smarter food preparation decisions.

## Project Goal

The main objective is to analyze how much food is prepared, consumed, and discarded across different meal periods and food items. By using data-driven insights, the canteen can:

- reduce unnecessary food waste
- improve inventory planning
- optimize meal preparation volumes
- support sustainability goals on campus
- reduce operating costs and resource loss

## Why This Project Matters

Food waste is a common problem in institutional kitchens, especially where demand varies daily. The canteen may prepare too much food due to uncertain student attendance, changing preferences, and seasonal demand fluctuations. This project helps convert raw daily operational data into clear business insights.

## Hadoop / Big Data Perspective

Although this project is implemented in a lightweight local environment, it follows the structure of a Big Data workflow commonly used in Hadoop and Spark ecosystems:

1. Data collection from canteen operations
2. Data cleaning and validation
3. Transformation of raw food data into analytical summaries
4. Aggregation by date, item, and meal type
5. Visualization and decision support

This is similar to how enterprises handle batch processing with Spark on Hadoop clusters, where large-scale datasets are transformed into actionable business intelligence.

## Dataset

The dataset contains daily records with fields such as:

- date
- food_item
- prepared_kg
- served_kg
- waste_kg
- meal

A sample record looks like:

```
2026-10-01,Rice,20,16,4,Lunch
```

The project analyzes:

- total amount prepared
- total amount consumed
- total amount wasted
- waste percentage by item and day
- utilization patterns by meal type

## Project Structure

```text
College Canteen Food Waste Analyzer/
├── data/
│   └── canteen_food_waste.csv
├── output/
│   └── app.py
├── src/
│   └── analyze.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Tech Stack

- Python
- Apache Spark
- Streamlit
- Plotly
- Pandas

## Workflow

### 1. Data Processing with Spark
The `src/analyze.py` script reads the CSV, cleans invalid records, converts fields to numeric types, and produces processed outputs for:

- daily summaries
- food item summaries
- meal-wise summaries
- overall waste insights

### 2. Dashboard Visualization
The `output/app.py` dashboard displays:

- total prepared / consumed / wasted quantities
- waste rate percentage
- food item comparison charts
- daily waste trend
- actionable recommendations
- downloadable CSV report

## Key Use Cases

- campus sustainability initiatives
- canteen planning and forecasting
- reducing food waste and cost
- identifying high-waste menu items
- creating smarter nutrition and procurement decisions

## How to Run

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the Spark analysis

```bash
python src/analyze.py
```

### Launch dashboard

```bash
streamlit run output/app.py
```

## Creative Enhancement Idea

This project can be extended with:

- real-time waste monitoring
- machine learning forecasting for demand prediction
- a dashboard with login and admin role access
- charts for wastage by day, meal, and student footfall
- export to PDF or Excel reports
- integration with IoT or cafeteria inventory systems

## Conclusion

This project demonstrates how Big Data tools and data visualization can solve a real-world sustainability problem in educational institutions. It combines analytics, operational efficiency, and campus responsibility into one practical and creative data project.
