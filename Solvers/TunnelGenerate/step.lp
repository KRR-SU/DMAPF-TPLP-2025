#program step(t).

time(t). 
{plan(A,t,X)} :- plan(A,t-1,X), agent(A).
{plan(A,t,Y): edge(X,Y), tunnel(A,Y)}1 :- plan(A,t-1,X), agent(A).


:- {plan(A,t,X): vertex(X)}0, agent(A). 
:- 2{plan(A,t,X): vertex(X)}, agent(A). 

% no two agents are at the same vertex at time T.
:- 2{plan(A,t,X): agent(A)}, vertex(X), time(t). 

% no swapping
plan_to(X,Y,t,0) :- plan(A,t-1,X), plan(A,t,Y), edge(X,Y), agent(A).
:- plan_to(X,Y,t,_), plan_to(Y,X,t,_).

% goal is reached if the agent visits it at some earlier time or now
goal_reached(A,t) :- goal(A,X), plan(A,t,X), agent(A).
goal_reached(A,t) :- goal_reached(A,t-1).


