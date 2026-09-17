import pandas as pd
#Testing
print("Bonjour !")

df = pd.read_csv(
    "regularite-mensuelle-tgv-aqst.csv",
    sep=";"
)


print(df.head(5))