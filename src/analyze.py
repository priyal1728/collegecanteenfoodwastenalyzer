import os
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def main() -> None:
    spark = (
        SparkSession.builder
        .appName("CollegeCanteenFoodWasteAnalyzer")
        .config("spark.sql.adaptive.enabled", "true")
        .getOrCreate()
    )

    try:
        project_root = Path(__file__).resolve().parents[1]
        input_path = os.environ.get("FOOD_WASTE_INPUT", str(project_root / "data" / "canteen_food_waste.csv"))
        output_path = os.environ.get("FOOD_WASTE_OUTPUT", str(project_root / "output"))

        df = spark.read.option("header", True).option("inferSchema", True).csv(input_path)

        required = {
            "date",
            "food_item",
            "prepared_kg",
            "served_kg",
            "waste_kg",
        }

        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Missing CSV columns: {sorted(missing)}")

        df = (
            df.withColumnRenamed("prepared_kg", "prepared_quantity")
            .withColumnRenamed("served_kg", "consumed_quantity")
            .withColumnRenamed("waste_kg", "wasted_quantity")
            .withColumn("date", F.to_date(F.col("date")))
            .withColumn("prepared_quantity", F.col("prepared_quantity").cast("double"))
            .withColumn("consumed_quantity", F.col("consumed_quantity").cast("double"))
            .withColumn("wasted_quantity", F.col("wasted_quantity").cast("double"))
            .withColumn(
                "waste_rate_percent",
                F.when(F.col("prepared_quantity") > 0,
                       (F.col("wasted_quantity") / F.col("prepared_quantity")) * 100
                ).otherwise(0.0),
            )
            .withColumn(
                "utilization_rate_percent",
                F.when(F.col("prepared_quantity") > 0,
                       (F.col("consumed_quantity") / F.col("prepared_quantity")) * 100
                ).otherwise(0.0),
            )
            .filter(
                F.col("date").isNotNull()
                & F.col("food_item").isNotNull()
                & F.col("prepared_quantity").isNotNull()
                & F.col("consumed_quantity").isNotNull()
                & F.col("wasted_quantity").isNotNull()
            )
        )

        daily_summary = (
            df.groupBy("date")
            .agg(
                F.sum("prepared_quantity").alias("total_prepared"),
                F.sum("consumed_quantity").alias("total_consumed"),
                F.sum("wasted_quantity").alias("total_wasted"),
            )
            .withColumn(
                "waste_rate_percent",
                F.when(F.col("total_prepared") > 0,
                       (F.col("total_wasted") / F.col("total_prepared")) * 100
                ).otherwise(0.0),
            )
            .withColumn(
                "utilization_rate_percent",
                F.when(F.col("total_prepared") > 0,
                       (F.col("total_consumed") / F.col("total_prepared")) * 100
                ).otherwise(0.0),
            )
            .orderBy("date")
        )

        food_item_summary = (
            df.groupBy("food_item")
            .agg(
                F.sum("prepared_quantity").alias("total_prepared"),
                F.sum("consumed_quantity").alias("total_consumed"),
                F.sum("wasted_quantity").alias("total_wasted"),
            )
            .withColumn(
                "waste_rate_percent",
                F.when(F.col("total_prepared") > 0,
                       (F.col("total_wasted") / F.col("total_prepared")) * 100
                ).otherwise(0.0),
            )
            .withColumn(
                "utilization_rate_percent",
                F.when(F.col("total_prepared") > 0,
                       (F.col("total_consumed") / F.col("total_prepared")) * 100
                ).otherwise(0.0),
            )
            .orderBy(F.col("total_wasted").desc())
        )

        meal_summary = (
            df.groupBy("meal")
            .agg(
                F.sum("prepared_quantity").alias("total_prepared"),
                F.sum("consumed_quantity").alias("total_consumed"),
                F.sum("wasted_quantity").alias("total_wasted"),
            )
            .withColumn(
                "waste_rate_percent",
                F.when(F.col("total_prepared") > 0,
                       (F.col("total_wasted") / F.col("total_prepared")) * 100
                ).otherwise(0.0),
            )
            .withColumn(
                "utilization_rate_percent",
                F.when(F.col("total_prepared") > 0,
                       (F.col("total_consumed") / F.col("total_prepared")) * 100
                ).otherwise(0.0),
            )
            .orderBy(F.col("total_wasted").desc())
            if "meal" in df.columns
            else None
        )

        overall_summary = (
            df.agg(
                F.sum("prepared_quantity").alias("total_prepared"),
                F.sum("consumed_quantity").alias("total_consumed"),
                F.sum("wasted_quantity").alias("total_wasted"),
            )
            .withColumn(
                "waste_rate_percent",
                F.when(F.col("total_prepared") > 0,
                       (F.col("total_wasted") / F.col("total_prepared")) * 100
                ).otherwise(0.0),
            )
            .withColumn(
                "utilization_rate_percent",
                F.when(F.col("total_prepared") > 0,
                       (F.col("total_consumed") / F.col("total_prepared")) * 100
                ).otherwise(0.0),
            )
        )

        os.makedirs(output_path, exist_ok=True)

        daily_summary.write.mode("overwrite").option("header", True).csv(f"{output_path}/daily_summary")
        food_item_summary.write.mode("overwrite").option("header", True).csv(f"{output_path}/food_item_summary")
        df.write.mode("overwrite").option("header", True).csv(f"{output_path}/cleaned_records")
        overall_summary.write.mode("overwrite").option("header", True).csv(f"{output_path}/overall_summary")

        if meal_summary is not None:
            meal_summary.write.mode("overwrite").option("header", True).csv(f"{output_path}/meal_summary")

        insights = [
            ("Total Prepared", overall_summary.collect()[0]["total_prepared"], "Total quantity prepared across the analyzed period."),
            ("Total Consumed", overall_summary.collect()[0]["total_consumed"], "Food actually consumed by students and staff."),
            ("Total Wasted", overall_summary.collect()[0]["total_wasted"], "Food lost due to over-preparation, leftover waste, or spoilage."),
            ("Waste Rate", overall_summary.collect()[0]["waste_rate_percent"], "Percentage of prepared food that ends up being discarded."),
        ]

        insights_df = spark.createDataFrame(insights, ["metric", "value", "description"])
        insights_df.write.mode("overwrite").option("header", True).csv(f"{output_path}/smart_insights")

        print("\n=== Smart Canteen Waste Dashboard Summary ===")
        overall_summary.show(truncate=False)

        print("\n=== Top Waste by Food Item ===")
        food_item_summary.show(truncate=False)

        if meal_summary is not None:
            print("\n=== Waste by Meal Type ===")
            meal_summary.show(truncate=False)

        print(f"\nAnalysis complete. Output generated in: {output_path}")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()