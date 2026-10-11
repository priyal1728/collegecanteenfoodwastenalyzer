
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum, to_date

spark = (
    SparkSession.builder
    .appName("CollegeCanteenFoodWasteAnalyzer")
    .getOrCreate()
)

try:
    input_path = os.environ.get(
    "FOOD_WASTE_INPUT",
    "file:///home/priyal123/college_canteen_food_waste_analyzer/data/canteen_food_waste.csv"
)

    output_path = os.environ.get(
        "FOOD_WASTE_OUTPUT",
        "output"
    )

    # Read dataset
    df = spark.read.option("header", True).option(
        "inferSchema", True
    ).csv(input_path)

    required = {
        "date",
        "food_item",
        "prepared_quantity",
        "consumed_quantity",
        "wasted_quantity",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing CSV columns: {sorted(missing)}")

    # Clean and validate data
    df = (
        df.withColumn("date", to_date(col("date")))
        .withColumn("prepared_quantity", col("prepared_quantity").cast("double"))
        .withColumn("consumed_quantity", col("consumed_quantity").cast("double"))
        .withColumn("wasted_quantity", col("wasted_quantity").cast("double"))
        .filter(
            col("date").isNotNull()
            & col("food_item").isNotNull()
            & col("prepared_quantity").isNotNull()
            & col("consumed_quantity").isNotNull()
            & col("wasted_quantity").isNotNull()
        )
    )

    print("\n--- Cleaned Canteen Records ---")
    df.show(truncate=False)

    # Daily waste summary
    daily = (
        df.groupBy("date")
        .agg(
            spark_sum("prepared_quantity").alias("total_prepared"),
            spark_sum("consumed_quantity").alias("total_consumed"),
            spark_sum("wasted_quantity").alias("total_wasted"),
        )
        .orderBy("date")
    )

    # Waste summary by food item
    by_item = (
        df.groupBy("food_item")
        .agg(
            spark_sum("prepared_quantity").alias("total_prepared"),
            spark_sum("consumed_quantity").alias("total_consumed"),
            spark_sum("wasted_quantity").alias("total_wasted"),
        )
        .orderBy(col("total_wasted").desc())
    )

    os.makedirs(output_path, exist_ok=True)

    daily.write.mode("overwrite").option("header", True).csv(
        f"{output_path}/daily"
    )
    by_item.write.mode("overwrite").option("header", True).csv(
        f"{output_path}/by_item"
    )
    df.write.mode("overwrite").option("header", True).csv(
        f"{output_path}/cleaned_records"
    )

    # Create meal summary only when the CSV has a meal column
    if "meal" in df.columns:
        by_meal = (
            df.groupBy("meal")
            .agg(                spark_sum("prepared_quantity").alias("total_prepared"),
                spark_sum("consumed_quantity").alias("total_consumed"),
                spark_sum("wasted_quantity").alias("total_wasted"),
            )
        )
        by_meal.write.mode("overwrite").option("header", True).csv(
            f"{output_path}/by_meal"
        )

    print("\n--- Waste by Food Item ---")
    by_item.show(truncate=False)
    print(f"Analysis complete. Results saved to: {output_path}")

finally:
    spark.stop()
