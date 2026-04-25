#program forbidden_locations.

forbidden_visited(A,T,X) :-  plan(A,T,X), forbidden(A,X), agent(A), time(T).
:- forbidden_visited(A,T,X).
