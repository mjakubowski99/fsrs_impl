from fsrs import Scheduler, Card, Rating as FsrsRating

scheduler = Scheduler(enable_fuzzing=False)

cards = [Card() for _ in range(10)]

names = [
    "Harsh",
    "Come over",
    "Yippee",
    "Come in",
    "vicious",
    "meticulous",
    "sarcastic",
    "cynical",
    "disgusting",
    "repulsive",
]

for card, name in zip(cards, names):
    card.name = name

while True:
    # sort cards by due date
    cards.sort(key=lambda c: c.due.timestamp())

    # pick the next due card
    card = cards[0]

    print(f"\nNext card: {card.name}")
    print(f"Due: {card.due}")
    print("Rating (1=Again, 2=Hard, 3=Good, 4=Easy) or 'exit': ", end="")

    rating_input = input().strip().lower()
    if rating_input == "exit":
        break

    if rating_input not in {"1", "2", "3", "4"}:
        print("Invalid rating. Try again.")
        continue

    rating = FsrsRating(int(rating_input))

    updated_card, review_log = scheduler.review_card(card, rating)

    # replace the card in the list
    cards[0] = updated_card

    print(f"New due: {updated_card.due}")
