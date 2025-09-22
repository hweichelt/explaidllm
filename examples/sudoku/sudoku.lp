number(1..4).
sudoku(X,Y,N) :- initial(X,Y,N).
1{sudoku(X,Y,N): number(N)}1 :- number(X), number(Y).
:- sudoku(X1,Y,N), sudoku(X2,Y,N), X1>X2.
:- sudoku(X,Y1,N), sudoku(X,Y2,N), Y1>Y2.
subgrid(X1,Y1,X2,Y2) :- sudoku(X1,Y1,_), sudoku(X2,Y2,_),
                        ((X1-1)/2)==((X2-1)/2),
                        ((Y1-1)/2)==((Y2-1)/2).
:- subgrid(X1,Y1,X2,Y2), sudoku(X1,Y1,N), sudoku(X2,Y2,N), X1!=X2, Y1!=Y2.
