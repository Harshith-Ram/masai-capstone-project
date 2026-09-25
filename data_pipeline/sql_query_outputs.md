# SQL Query Outputs

## q1_select_where

```sql
SELECT title, price_gbp, rating
            FROM books
            WHERE rating >= 4
            ORDER BY rating DESC, price_gbp DESC
            LIMIT 10
```

| title                                                                    |   price_gbp |   rating |
|:-------------------------------------------------------------------------|------------:|---------:|
| A Flight of Arrows (The Pathfinders #2)                                  |       55.53 |        5 |
| The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1) |       52.3  |        5 |
| A Time of Torment (Charlie Parker #14)                                   |       48.35 |        5 |
| While You Were Mine                                                      |       41.32 |        5 |
| The Red Tent                                                             |       35.66 |        5 |
| Mrs. Houdini                                                             |       30.25 |        5 |
| The Passion of Dolssa                                                    |       28.32 |        5 |
| 1,000 Places to See Before You Die                                       |       26.08 |        5 |
| What Happened on Beale Street (Secrets of the South Mysteries #2)        |       25.37 |        5 |
| The Silkworm (Cormoran Strike #2)                                        |       23.05 |        5 |

## q2_distinct

```sql
SELECT DISTINCT c.category_name
            FROM categories c
            ORDER BY c.category_name
```

| category_name      |
|:-------------------|
| Historical Fiction |
| Mystery            |
| Travel             |

## q3_between

```sql
SELECT title, price_gbp
            FROM books
            WHERE price_gbp BETWEEN 20 AND 40
            ORDER BY price_gbp ASC
            LIMIT 10
```

| title                                                                                             |   price_gbp |
|:--------------------------------------------------------------------------------------------------|------------:|
| Blood Defense (Samantha Brinkman #1)                                                              |       20.3  |
| Love, Lies and Spies                                                                              |       20.55 |
| Between Shades of Gray                                                                            |       20.79 |
| Delivering the Truth (Quaker Midwife Mystery #1)                                                  |       20.89 |
| Voyager (Outlander #3)                                                                            |       21.07 |
| The Silkworm (Cormoran Strike #2)                                                                 |       23.05 |
| The Road to Little Dribbling: Adventures of an American in Britain (Notes From a Small Island #2) |       23.21 |
| Career of Evil (Cormoran Strike #3)                                                               |       24.72 |
| The Mysterious Affair at Styles (Hercule Poirot #1)                                               |       24.8  |
| What Happened on Beale Street (Secrets of the South Mysteries #2)                                 |       25.37 |

## q4_in_clause

```sql
SELECT title, rating, price_gbp
            FROM books
            WHERE rating IN (4, 5)
            ORDER BY price_gbp DESC
            LIMIT 10
```

| title                                                                    |   rating |   price_gbp |
|:-------------------------------------------------------------------------|---------:|------------:|
| The No. 1 Ladies' Detective Agency (No. 1 Ladies' Detective Agency #1)   |        4 |       57.7  |
| A Year in Provence (Provence #1)                                         |        4 |       56.88 |
| The Past Never Ends                                                      |        4 |       56.5  |
| A Flight of Arrows (The Pathfinders #2)                                  |        5 |       55.53 |
| Murder at the 42nd Street Library (Raymond Ambler #1)                    |        4 |       54.36 |
| The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1) |        5 |       52.3  |
| Full Moon over Noah’s Ark: An Odyssey to Mount Ararat and Beyond         |        4 |       49.43 |
| A Time of Torment (Charlie Parker #14)                                   |        5 |       48.35 |
| Sharp Objects                                                            |        4 |       47.82 |
| The Murder of Roger Ackroyd (Hercule Poirot #4)                          |        4 |       44.1  |

## q5_join

```sql
SELECT b.title, b.rating, b.price_gbp, c.category_name
            FROM books b
            JOIN categories c ON b.category_id = c.category_id
            ORDER BY b.rating DESC, b.price_gbp DESC
            LIMIT 15
```

| title                                                                    |   rating |   price_gbp | category_name      |
|:-------------------------------------------------------------------------|---------:|------------:|:-------------------|
| A Flight of Arrows (The Pathfinders #2)                                  |        5 |       55.53 | Historical Fiction |
| The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1) |        5 |       52.3  | Mystery            |
| A Time of Torment (Charlie Parker #14)                                   |        5 |       48.35 | Mystery            |
| While You Were Mine                                                      |        5 |       41.32 | Historical Fiction |
| The Red Tent                                                             |        5 |       35.66 | Historical Fiction |
| Mrs. Houdini                                                             |        5 |       30.25 | Historical Fiction |
| The Passion of Dolssa                                                    |        5 |       28.32 | Historical Fiction |
| 1,000 Places to See Before You Die                                       |        5 |       26.08 | Travel             |
| What Happened on Beale Street (Secrets of the South Mysteries #2)        |        5 |       25.37 | Mystery            |
| The Silkworm (Cormoran Strike #2)                                        |        5 |       23.05 | Mystery            |
| Voyager (Outlander #3)                                                   |        5 |       21.07 | Historical Fiction |
| Between Shades of Gray                                                   |        5 |       20.79 | Historical Fiction |
| A Spy's Devotion (The Regency Spies of London #1)                        |        5 |       16.97 | Historical Fiction |
| The Girl You Lost                                                        |        5 |       12.29 | Mystery            |
| The No. 1 Ladies' Detective Agency (No. 1 Ladies' Detective Agency #1)   |        4 |       57.7  | Mystery            |

## Pandas read_sql Demonstration

read_sql result (Query 1):

| title                                                                    |   price_gbp |   rating |
|:-------------------------------------------------------------------------|------------:|---------:|
| A Flight of Arrows (The Pathfinders #2)                                  |       55.53 |        5 |
| The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1) |       52.3  |        5 |
| A Time of Torment (Charlie Parker #14)                                   |       48.35 |        5 |
| While You Were Mine                                                      |       41.32 |        5 |
| The Red Tent                                                             |       35.66 |        5 |
| Mrs. Houdini                                                             |       30.25 |        5 |
| The Passion of Dolssa                                                    |       28.32 |        5 |
| 1,000 Places to See Before You Die                                       |       26.08 |        5 |
| What Happened on Beale Street (Secrets of the South Mysteries #2)        |       25.37 |        5 |
| The Silkworm (Cormoran Strike #2)                                        |       23.05 |        5 |

read_sql result (JOIN query):

| title                                                                    |   rating |   price_gbp | category_name      |
|:-------------------------------------------------------------------------|---------:|------------:|:-------------------|
| A Flight of Arrows (The Pathfinders #2)                                  |        5 |       55.53 | Historical Fiction |
| The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1) |        5 |       52.3  | Mystery            |
| A Time of Torment (Charlie Parker #14)                                   |        5 |       48.35 | Mystery            |
| While You Were Mine                                                      |        5 |       41.32 | Historical Fiction |
| The Red Tent                                                             |        5 |       35.66 | Historical Fiction |
| Mrs. Houdini                                                             |        5 |       30.25 | Historical Fiction |
| The Passion of Dolssa                                                    |        5 |       28.32 | Historical Fiction |
| 1,000 Places to See Before You Die                                       |        5 |       26.08 | Travel             |
| What Happened on Beale Street (Secrets of the South Mysteries #2)        |        5 |       25.37 | Mystery            |
| The Silkworm (Cormoran Strike #2)                                        |        5 |       23.05 | Mystery            |
| Voyager (Outlander #3)                                                   |        5 |       21.07 | Historical Fiction |
| Between Shades of Gray                                                   |        5 |       20.79 | Historical Fiction |
| A Spy's Devotion (The Regency Spies of London #1)                        |        5 |       16.97 | Historical Fiction |
| The Girl You Lost                                                        |        5 |       12.29 | Mystery            |
| The No. 1 Ladies' Detective Agency (No. 1 Ladies' Detective Agency #1)   |        4 |       57.7  | Mystery            |

## Pandas merge Demonstration (No SQL)

| title                                                                    |   rating |   price_gbp | category_name      |
|:-------------------------------------------------------------------------|---------:|------------:|:-------------------|
| A Flight of Arrows (The Pathfinders #2)                                  |        5 |       55.53 | Historical Fiction |
| The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1) |        5 |       52.3  | Mystery            |
| A Time of Torment (Charlie Parker #14)                                   |        5 |       48.35 | Mystery            |
| While You Were Mine                                                      |        5 |       41.32 | Historical Fiction |
| The Red Tent                                                             |        5 |       35.66 | Historical Fiction |
| Mrs. Houdini                                                             |        5 |       30.25 | Historical Fiction |
| The Passion of Dolssa                                                    |        5 |       28.32 | Historical Fiction |
| 1,000 Places to See Before You Die                                       |        5 |       26.08 | Travel             |
| What Happened on Beale Street (Secrets of the South Mysteries #2)        |        5 |       25.37 | Mystery            |
| The Silkworm (Cormoran Strike #2)                                        |        5 |       23.05 | Mystery            |
| Voyager (Outlander #3)                                                   |        5 |       21.07 | Historical Fiction |
| Between Shades of Gray                                                   |        5 |       20.79 | Historical Fiction |
| A Spy's Devotion (The Regency Spies of London #1)                        |        5 |       16.97 | Historical Fiction |
| The Girl You Lost                                                        |        5 |       12.29 | Mystery            |
| The No. 1 Ladies' Detective Agency (No. 1 Ladies' Detective Agency #1)   |        4 |       57.7  | Mystery            |

Join-equivalence check: **True**
