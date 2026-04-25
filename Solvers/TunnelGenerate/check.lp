#program check(t).
#external query(t).

% there exists an incoming edge to goal
:- not goal_reached(A,t), agent(A), query(t).

% make sure agent ends at goal
:- not goal(A,X), plan(A,t,X), agent(A), query(t). 

