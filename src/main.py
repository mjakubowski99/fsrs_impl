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

# fsrs = FsrsParams()

# while (True):
#     rating = input('Rating: ')
#     if rating == 'exit':
#         break
#     fsrs.review(Rating(int(rating)))
#     card, review_log = scheduler.review_card(card, FsrsRating(int(rating)))

#     print(f"Stability: {fsrs.stability}, {card.stability}")
#     assert fsrs.stability == card.stability
#     print(f"Difficulty: {fsrs.difficulty}, {card.difficulty}")
#     assert fsrs.difficulty == card.difficulty
#     print(f"Due: {fsrs.due}, {card.due}")
#     diff = abs((fsrs.due - card.due).total_seconds())
#     if diff > 1.5:  # Accept up to 1.5 seconds difference
#         raise AssertionError(f"Due datetime differs too much: {fsrs.due} vs {card.due} (difference {diff} seconds)")
#     print(f"Last Review: {fsrs.last_review}, {card.last_review}")
#     diff = abs((fsrs.last_review - card.last_review).total_seconds())
#     if diff > 1.5:  # Accept up to 1.5 seconds difference
#         raise AssertionError(f"Last review datetime differs too much: {fsrs.last_review} vs {card.last_review} (difference {diff} seconds)")
#     print(f"Step: {fsrs.step}, {card.step}")
#     assert fsrs.step == card.step
#     print('Ok')