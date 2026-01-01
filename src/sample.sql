
SELECT * FROM flashcards 
LEFT JOIN fsrs ON flashcards.id = fsrs.card_id
# lista filtrow sql 
WHERE 
    (lista warunkow fsrs w postaci or where zeby db moglo zakonczyc po znalezieniu pierwszego pasujacego rekordu)
ORDER BY
    CASE 
        WHEN fsrs.stability > 3 and fsrs.next_review_date <= NOW() THEN 1
        WHEN fsrs.stability <= 3 and fsrs.next_review_date <= NOW() THEN 2
        WHEN fsrs.is_pending is true THEN 3 
        WHEN fsrs.reviews_count = 0 THEN 4
        ELSE 3
    END,
    fsrs.next_review_date ASC
LIMIT 1;