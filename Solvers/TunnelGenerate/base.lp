#program base.

plan(A,0,X) :- init(A,X), agent(A).
time(0).
agent_added(A,0) :- agent(A).
