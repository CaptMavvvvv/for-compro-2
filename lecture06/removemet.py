fruits_with_duplicates = ["apple", "banana", "apple", "cheery", "apple", "kiwi"]
while "apple" in fruits_with_duplicates:
    fruits_with_duplicates.remove("apple")
print(fruits_with_duplicates)