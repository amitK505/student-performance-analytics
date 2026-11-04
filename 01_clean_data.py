import pandas as pandas

# Read CSV file
df = pandas.read_csv("data/raw_students.csv")

# understand the dataset

print("First rows:")
print(df.head())

print("\nDataset shape:")
print(df.shape)

print("\nData types:")
df.info()

print("\nMissing values:")
print(df.isnull().sum())

print("\nDuplicate student IDs:")
print(df.duplicated(subset=["student_id"]).sum())


# remove duplicate students
df = df.drop_duplicates(
    subset=["student_id"],
    keep="first"
)

#Convert numerics columns

number_columns = [
    "math_marks",
    "science_marks",
    "english_marks",
    "attendance"
]

for column in number_columns:
    df[column] = pandas.to_numeric(
        df[column],
        errors="coerce"
    )

    df[column] = df[column].fillna(
        df[column].median()
    )

    #keep values bettwen 0 and 100
    df[column] = df[column].clip(0,100)

# Clean text columns
df["student_name"]= (
    df["student_name"].fillna("Unknown").str.strip()
)

df["department"] = (
    df["department"].fillna("Unknown").str.strip()
)

# Save cleaned dataset
df.to_csv("data/cleaned_student.csv", index=False)

print("\nCleaning Completed!")
print("Final student count:",len(df))