import numpy as np
from numpy import linalg as la
from tabulate import tabulate


def estimate( 
        y, x, z=None, transform='', T=None, robust_se=False
    ) -> list:
    """Uses the OLS or PIV to perform a regression of y on x, or z as an
    instrument if provided, and provides all other necessary statistics such 
    as standard errors, t-values etc.  

    Args:
        y (np.array): Dependent variable (Needs to have shape 2D shape)
        x (np.array): Independent variable (Needs to have shape 2D shape)
        z (None or np.array): Instrument array (Needs to have same shape as x)
        >> transform (str, optional): Defaults to ''. If the data is 
        transformed in any way, the following transformations are allowed:
            '': No transformations
            'fd': First-difference
            'be': Between transformation
            'fe': Within transformation
            're': Random effects estimation.
        >> T (int, optional): If panel data, T is the number of time periods in
        the panel, and is used for estimating the variance. Defaults to None.
        >> robust_se (bool): Calculates robust standard errors if True.
        Defaults to False.

    Returns:
        list: Returns a dictionary with the following variables:
        'b_hat', 'se', 'sigma2', 't_values', 'R2', 'cov'
    """
    
    assert y.ndim == 2, 'Input y must be 2-dimensional'
    assert x.ndim == 2, 'Input x must be 2-dimensional'
    assert y.shape[1] == 1, 'y must be a column vector'
    assert y.shape[0] == x.shape[0], 'y and x must have same first dimension'
    
    if z is None: 
        b_hat = est_ols(y, x)
    else: 
        b_hat = est_piv(y, x, z)
    
    residual = y - x@b_hat
    SSR = np.sum(residual ** 2)
    SST = np.sum((y-y.mean()) ** 2)
    R2 = 1.0 - SSR/SST

    # If estimating piv, transform x before we calculating variance:
    if z is not None:
        x_ = None # fill in 
        R2 = np.array(np.nan)
    else: 
        x_ = x

    sigma2, cov, se = variance(transform, SSR, x_, T)
    if robust_se:
        cov, se = robust(x_, residual, T)
    t_values = b_hat/se
    
    names = ['b_hat', 'se', 'sigma2', 't_values', 'R2', 'cov']
    results = [b_hat, se, sigma2, t_values, R2, cov]
    return dict(zip(names, results))

    
def est_ols( y: np.array, x: np.array) -> np.array:
    """Estimates y on x by ordinary least squares, returns coefficents

    Args:
        >> y (np.array): Dependent variable (Needs to have shape 2D shape)
        >> x (np.array): Independent variable (Needs to have shape 2D shape)
    
    Returns:
        np.array: Estimated beta coefficients.
    """
    return la.inv(x.T@x)@(x.T@y)


def est_piv( y: np.array, x: np.array, z: np.array) -> np.array:
    """Estimates y on x, using z as instruments, then estimating by ordinary 
    least squares, returns coefficents

    Args:
        >> y (np.array): Dependent variable (Needs to have shape 2D shape)
        >> x (np.array): Independent variable (Needs to have shape 2D shape)
        >> z (np.array): Instrument array (Needs to have same shape as x)

    Returns:
        np.array: Estimated beta coefficients.
    """
    
    betahat =  None # FILL IN: Estimate betahat and return it 
    return betahat 

def variance( 
        transform: str, 
        SSR: float, 
        x: np.array, 
        T: int
    ) -> tuple:
    """Calculates the covariance and standard errors from the OLS
    estimation.

    Args:
        >> transform (str): Defaults to ''. If the data is transformed in 
        any way, the following transformations are allowed:
            '': No transformations
            'fd': First-difference
            'be': Between transformation
            'fe': Within transformation
            're': Random effects estimation
        >> SSR (float): Sum of squared residuals
        >> x (np.array): Dependent variables from regression
        >> t (int): The number of time periods in x.

    Raises:
        Exception: If invalid transformation is provided, returns
        an error.

    Returns:
        tuple: Returns the error variance (mean square error), 
        covariance matrix and standard errors.
    """
    # Store n and k, used for DF adjustments.
    Nrows,K = x.shape

    assert transform in ('', 'fd', 'be', 'fe', 're'), f'Transform, "{transform}", not implemented.'

    if transform in ('', 'fd', 'be', 're'):
        denom = Nrows - K
    elif transform == 'fe': 
        N = x.shape[0]/T
        denom = Nrows - N - K 

    sigma2 = SSR / denom 
    
    cov = sigma2*la.inv(x.T@x)
    se = np.sqrt(cov.diagonal()).reshape(-1, 1)

    return sigma2, cov, se


def robust( x: np.array, residual: np.array, T:int) -> tuple:
    '''Calculates the robust variance estimator 

    ARGS: 
        t: number of time periods 
    '''
    # If only cross sectional, we can easily use the diagonal.
    if not T:
        Ainv = la.inv(x.T@x)
        uhat2 = residual ** 2
        uhat2_x = uhat2 * x # elementwise multiplication: avoids forming the diagonal matrix (RAM intensive!)
        cov = Ainv @ (x.T@uhat2_x) @ Ainv
    
    # Else we loop over each individual.
    else:
        Sum= 0
        N = int(x.shape[0]/T) #Finder antal individer, ved at tage antal rækker på x-aksen divideret med antal time periods.
        Ainv = la.inv(x.T@x)
        for i in range(N):
            x_i =x[i*T : (i+1)*T,:] #vi starter individ i og ganger med t. så fortsætter vi til individet bagefter. 
            res_i = residual[i*T : (i+1)*T,:]
            u_x = res_i.T @ x_i
            x_u = u_x.T
            Sum += x_u@u_x        
        cov = Ainv @ Sum @ Ainv
    se = np.sqrt(np.diag(cov)).reshape(-1, 1)
    return cov, se


def print_table(
        labels: tuple,
        results: dict,
        headers=["", "Beta", "Se", "t-values"],
        title="Results",
        _lambda:float=None,
        **kwargs
    ) -> None:
    """Prints a nice looking table, must at least have coefficients, 
    standard errors and t-values. The number of coefficients must be the
    same length as the labels.

    Args:
        >> labels (tuple): Touple with first a label for y, and then a list of 
        labels for x.
        >> results (dict): The results from a regression. Needs to be in a 
        dictionary with at least the following keys:
            'b_hat', 'se', 't_values', 'R2', 'sigma2'
        >> headers (list, optional): Column headers. Defaults to 
        ["", "Beta", "Se", "t-values"].
        >> title (str, optional): Table title. Defaults to "Results".
        _lambda (float, optional): Only used with Random effects. 
        Defaults to None.
    """
    
    # Unpack the labels
    label_y, label_x = labels
    assert isinstance(label_x, list), f'label_x must be a list (second part of the tuple, labels)'
    assert len(label_x) == results['b_hat'].size, f'Number of labels for x should be the same as number of estimated parameters'
    
    # Create table, using the label for x to get a variable's coefficient,
    # standard error and t_value.
    table = []
    for i, name in enumerate(label_x):
        row = [
            name, 
            results.get('b_hat')[i], 
            results.get('se')[i], 
            results.get('t_values')[i]
        ]
        table.append(row)
    
    # Print the table
    print(title)
    print(f"Dependent variable: {label_y}\n")
    print(tabulate(table, headers, **kwargs))
    
    # Print extra statistics of the model.
    print(f"R\u00b2 = {results.get('R2').item():.3f}")
    print(f"\u03C3\u00b2 = {results.get('sigma2').item():.3f}")
    if _lambda: 
        print(f'\u03bb = {_lambda.item():.3f}')


def perm( Q_T: np.array, A: np.array) -> np.array:
    """Takes a transformation matrix and performs the transformation on 
    the given vector or matrix.

    Args:
        Q_T (np.array): The transformation matrix. Needs to have the same
        dimensions as number of years a person is in the sample.
        
        A (np.array): The vector or matrix that is to be transformed. Has
        to be a 2d array.

    Returns:
        np.array: Returns the transformed vector or matrix.
    """
    # We can infer T from the shape of the transformation matrix.
    M,T = Q_T.shape 
    N = int(A.shape[0]/T)
    K = A.shape[1]

    # initialize output 
    Z = np.empty((M*N, K))
    
    for i in range(N): 
        ii_A = slice(i*T, (i+1)*T)
        ii_Z = slice(i*M, (i+1)*M)
        Z[ii_Z, :] = Q_T @ A[ii_A, :]

    return Z


