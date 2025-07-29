animals = ["cat", "dog", "rabbit", "hamster", "dog", "parrot"]
first_dog_index = animals.index("dog")
print(first_dog_index)

second_dog_index = animals.index("dog", first_dog_index + 1)
print(second_dog_index)