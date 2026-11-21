

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy.optimize import fsolve
from scipy.optimize import minimize


from enum import Enum

class ConvergenceType(Enum):
    """
    Enum to represent different types of convergence and divergence behavior, used to
    characterize the convergence of a triplet of QOI values.
    
    Attributes:
        MONOTONIC_CONVERGENCE: Values converge in a monotonic manner.
        OSCILLATORY_CONVERGENCE: Values converge in an oscillatory manner.
        MONOTONIC_DIVERGENCE: Values diverge monotonically.
        OSCILLATORY_DIVERGENCE: Values diverge in an oscillatory manner.
    """
    MONOTONIC_CONVERGENCE = 0
    OSCILLATORY_CONVERGENCE = 1
    MONOTONIC_DIVERGENCE = 2
    OSCILLATORY_DIVERGENCE = 3



class CalculationVerificationTool():
    """
    Class to perform various calculations and analyses related to convergence verification
    """
    def __init__(self, suppress_output = False, use_absolute_GCI = True):
        """
        Initializes an instance of CalculationVerificationTool.
        Parameters:
            suppress_output (bool): whether to suppress text output during calculation. Defaults to False
            use_absolute_GCI (bool): whether to compute absolute GCI. 
            Defaults to True. If False relative GCI is returned as a dimensionless fraction (not percentage)
        """
        # Intialize attributes
        self._reset()

        # method that will used to compute the metrics. See _determine_method()
        self.method = None # outside of _reset as want this to persist after being set. 

        self.suppress_output = suppress_output
        self.use_absolute_GCI = use_absolute_GCI


    def _print(self, message):
        """
        Simply prints the message if the suppress_output flag is false

        """
        if not self.suppress_output:
            print(message)

    def _reset(self):
        """ 
        Reset class attributes
        """
        # pandas dataframe of metrics for intermediate triplet. 
        self.intermediate_triplet_metrics = None
        # dictionary storing the least squares curve fit
        self.ls_fit_curve = None     
        
        # stores of the last inputs used and the last outputs created
        self.last_h_values = None
        self.last_qoi_values = None
        self.last_ooc = None
        self.last_re = None
        self.last_gci = None
        
        self.x_label = "h"


    def _check_oscillatory_status(self,q1,q2,q3):
        """
        Determines the convergence or divergence type for a triplet of quantities.
        
        Given three function values (q1, q2, q3) corresponding to solutions on the 
        finest, medium, and coarse meshes, this function computes a ratio R and 
        uses it to classify the convergence/divergence as either monotonic or 
        oscillatory.
        
        Parameters:
            q1 (float): QOI value on the finest mesh.
            q2 (float): QOI value on the medium mesh.
            q3 (float): QOI value on the coarse mesh.
            
        Returns:
            ConvergenceType: An enum member indicating the type of convergence/divergence.
        """
        R = (q1-q2)/(q2-q3)
    
        if R >= 0 and R < 1:
            return ConvergenceType.MONOTONIC_CONVERGENCE
        elif R >= 1:
            return ConvergenceType.MONOTONIC_DIVERGENCE
        elif R < 0 and R > -1:
            return ConvergenceType.OSCILLATORY_CONVERGENCE
        else: # R <= -1:
            return ConvergenceType.OSCILLATORY_DIVERGENCE
    

    def _save_results(self, h_values, qoi_values, ooc, re, gci):
        self.last_h_values = h_values
        self.last_qoi_values = qoi_values
        self.last_ooc = ooc
        self.last_re = re
        self.last_gci = gci
        
        
    def _determine_method(self, h_values, qoi_values):
        """
        Determines the appropriate method for convergence analysis based on the provided mesh sizes and QOI values.
        
        Implements the following
          * if N=3
              * if monotonic convergence, can calculate metrics using this triplet
              * if oscillatory convergence, exit with message to the user
              * if divergence, exit with message to the user
          * if N>3
              * if monotonic convergence on first triplet, analyze each triplet
              * if oscillatory convergence on first triplet, use least squares method
              * if divergence on first triplet, exit with message to the user
        
        Parameters:
            h_values (list or array-like): Mesh sizes.
            qoi_values (list or array-like): Quantities of interest corresponding to each mesh size.
            
        Returns:
            str: Method name indicating the type of analysis to be performed.
        """
        # Ensure that h_values and qoi_values have the same length
        if len(h_values) != len(qoi_values):
            raise ValueError("h_values and qoi_values must have the same length")
    
        # Need at least 3 values to compute convergence metrics
        N = len(h_values)
        if N<3:
            raise ValueError("h_values and qoi_values must be of size 3 or more")
    
        # check the h_values are increasing
        assert(h_values[0]>0)                
        if not np.all(np.diff(h_values) > 0):
            raise ValueError("h_values must be strictly increasing")    
            
        if np.min(np.abs(np.diff(qoi_values)))<1e-14:
            raise ValueError("Two consecutive values in qoi_values are equal - provide greater precision values")
            
        
        # Check convergence status for the first three QOI values
        q1 = qoi_values[0]
        q2 = qoi_values[1]
        q3 = qoi_values[2]
    
        conv_type = self._check_oscillatory_status(q1,q2,q3)

        if N == 3:
            if conv_type in [ConvergenceType.MONOTONIC_DIVERGENCE,ConvergenceType.OSCILLATORY_DIVERGENCE]:
                self._print("QOI values diverging. Add QOI values for finer meshes")
                return "cannot_run"
            elif conv_type == ConvergenceType.OSCILLATORY_CONVERGENCE:
                self._print("QOI values oscillatory - cannot compute metrics when N=3. Repeat with N>3 meshes.")
                return "cannot_run"
            else:
                self._print("Method: standard method, as N=3 and monotonically converging")
                gci_string = "Absolute GCI not relative GCI" if self.use_absolute_GCI else "Relative GCI not absolute GCI"
                self._print(gci_string)                
                return 'N3_mono'
        else: # N>3
            if conv_type in [ConvergenceType.MONOTONIC_DIVERGENCE,ConvergenceType.OSCILLATORY_DIVERGENCE]:
                self._print("QOI on finest three meshes is diverging. Add QOI values for finer meshes")
                return "cannot_run"
            elif conv_type == ConvergenceType.OSCILLATORY_CONVERGENCE:
                self._print("Method: least squares, as N>3 and QOI on finest three meshes is converging but oscillatory")
                gci_string = "Absolute GCI not relative GCI" if self.use_absolute_GCI else "Relative GCI not absolute GCI"
                self._print(gci_string)                
                return "least_squares"
            else: 
                self._print("Method: analyzing each triplet, as N>3 and QOI on finest\nthree meshes is monotonically converging")                
                gci_string = "Absolute GCIs not relative GCIs" if self.use_absolute_GCI else "Relative GCIs not absolute GCIs"
                self._print(gci_string)    
                return "largeN_mono"
    
    
    

    def _compute_constrained_OOC(self, ooc, formal_order_conv, suppress_message = False, will_be_used_for_RE = True):
        """
        Constrains the computed OOC to be between 0.5 and the formal order (if provided)

        Parameters:
            ooc (float) : unconstrained OOC computed by solving the OOC equation
            formal_order_conv (float): formal order of convergence (could be None)
            suppress_message (bool): if True, suppresses printed message about the OOC being constrained for computing RE and GCI
            will_be_used_for_RE (bool): if True, warning message says ".. for calculating RE and GCI", if false, warning message only mentions GCI
        Returns
            (float) New OOC

        """
        used_in = "RE and GCI" if will_be_used_for_RE else "GCI"
        
        if ooc < 0.5:
            if not suppress_message:
                self._print(f"Note: OOC {ooc:.4f} < 0.5 - using 0.5 for calculating " + used_in)
            return 0.5

        if formal_order_conv is not None:
            if ooc < 0.9*formal_order_conv:
                return ooc
            elif ooc < formal_order_conv - 1e-12:
                if not suppress_message:
                    self._print(f"Note: OOC {ooc:.4f} < formal order, but within 10% - using formal order for calculating " + used_in)
                return formal_order_conv
            else:
                assert(ooc >= formal_order_conv - 1e-12)
                if not suppress_message:
                    self._print(f"Note: OOC {ooc:.4f} >= formal order - using formal order for calculating " + used_in)
                return formal_order_conv
        else:
            return ooc


    def _calculate_GCI(self, r21, q1, q2, ooc, constrained_ooc, formal_order_conv = None):
        """
        Calculates the Grid Convergence Index (GCI) based on provided parameters.
        
        Parameters:
            r21 (float): Ratio of mesh sizes for finest two meshes (h2/h1)
            q1 (float): QOI value on the finest mesh.
            q2 (float): QOI value on the next finest mesh.
            ooc (float): Observed Order of Convergence.
            constrained_ooc (float):The constrained OOC, often denoted p_GCI. This is passed in as will already have been computed by _compute_constrained_OOC. 
            formal_order_conv (float, optional): Formal order of convergence, if known.
            
        Returns:
            float: Calculated Grid Convergence Index (GCI - same units as QOI if default absolute GCI option used - see constructor)
        """        
        if formal_order_conv == None:
            Fs = 3
        else:
            assert(formal_order_conv>0)
            # safety factor based on how close ooc is to the formal order
            if np.abs(ooc - formal_order_conv) <= 0.1*formal_order_conv:
                Fs = 1.25
            else:
                Fs = 3
        
        gci = (Fs/(r21**constrained_ooc-1))*np.abs(q2-q1)
        
        if not self.use_absolute_GCI:
            if q1 == 0:
                raise ValueError("Requested relative GCI but QOI on finest mesh is zero")   
            gci = gci / np.abs(q1)
            
        return gci
    


    def analyze(self,h_values,qoi_values,formal_order_conv = None):
        """
        Analyzes convergence metrics (Observed Order of Convergence, Richardson Extrapolated value,
        and Grid Convergence Index) for a set of mesh sizes (h_values) and corresponding QOI values.
        
        For three values, it uses a specialized function; for more than three values, it uses a
        different approach and also collects results for multiple triplets.
        
        Parameters:
            h_values (list or array-like): Mesh sizes in strictly increasing order.
            qoi_values (list or array-like): Quantities of interest corresponding to each mesh size.
            formal_order_conv (float, optional): Formal order of convergence, if known.
            plot_axis_labels (tuple, optional): Axis labels for the plot as (xlabel, ylabel).
        
        Returns:
            tuple: (ooc, re, GCI)
                - ooc: Observed Order of Convergence.
                - re: Richardson Extrapolated value.
                - GCI: Grid Convergence Index (same units as QOI if default absolute GCI option used - see constructor).
            If errors occur (divergence, or oscillatory convergnece for the case of three grids), returns (None, None, None).
        """
        self._reset()
        
        # Determine the method to be used
        self.method = self._determine_method(h_values, qoi_values)
        
        assert(self.method in ["cannot_run", "N3_mono", "least_squares", "largeN_mono"])
        
        if self.method == "cannot_run":
            return None, None, None        
        elif self.method == "N3_mono":
            ooc, re, gci, error = self.analyze_N3_case(h_values,qoi_values,formal_order_conv)
            assert(error == None) # since determine_method already checked 
        elif self.method == "least_squares":
            ooc, re, gci = self.analyze_using_least_squares_method(h_values,qoi_values,formal_order_conv)
        else: # method == largeN_mono
            ooc, re, gci = self.analyze_largeN_mono_case(h_values,qoi_values,formal_order_conv)


        self._save_results(h_values, qoi_values, ooc, re, gci)
        return ooc, re, gci
 
    
 
    def analyze_by_n_elems(self,element_counts,dimension,qoi_values,formal_order_conv = None):
        """
        Analyzes and plots convergence metrics given element (cell) totals for each mesh instead of h values. Creates a vector of effective
        h values and calls analyze()
        
        Parameters:
            element_counts (array-like): Number of total elements for each mesh. Should be decreasing (finest mesh to coarsest mesh)
            dimension (int): Dimensionality of the grid - 1 to 3 inclusive
            qoi_values (array-like): Quantities of interest (QOI) values.
            formal_order_conv (float, optional): Formal order of convergence, if known.
            
        Returns:
            tuple: (ooc, re, GCI)
                - ooc (float): Observed Order of Convergence.
                - re (float): Richardson Extrapolated value.
                - GCI (float): Grid Convergence Index (same units as QOI if default absolute GCI option used - see constructor).
            If errors occur (divergence, or oscillatory convergnece for the case of three grids), returns (None, None, None).
        """
        self._reset()
        
        # check element counts are decreasing
        element_counts = np.array(element_counts)
        assert(element_counts[0]>0)                
        if not np.all(np.diff(element_counts) < 0):
            raise ValueError("element_counts must be strictly decreasing")   
        
        assert(dimension >= 1 and dimension <=3)

        # calculate an effective h array and call analyze()
        effective_mesh_ratio = (element_counts[0]/element_counts)**(1/dimension)
                
        ooc, re, gci = self.analyze(effective_mesh_ratio,qoi_values,formal_order_conv)
        
        # needs to be after the analyze call above, otherwise will impacted by _reset call
        self.x_label = "mesh refinement ratio (relative to finest)"
        
        return ooc, re, gci


    
    def analyze_N3_case(self,h_values,qoi_values,formal_order_conv = None, is_intermediate_triplet = False):
        """
        Analyzes convergence metrics for the case when exactly 3 mesh sizes are provided.
        
        It computes the observed order of convergence (ooc) and Richardson extrapolated value (re)
        using either a direct formula (grid refinement ratio, r, is constant) or by solving a nonlinear equation 
        when r21 = h2/h1 is not equal to r32 = h3/h2.
        
        Parameters:
            h_values (list or array-like): Mesh sizes in strictly increasing order.
            qoi_values (list or array-like): QOI values corresponding to the 3 meshes.
            formal_order_conv (float, optional): Formal order of convergence. 
            is_intermediate_triplet (boolean, optional, defaults to False): pass True when an intermediate triplet is
               being analyzed (so the results are not saved to the final store)
        
        Returns:
            tuple: (ooc, re, GCI, error)
                - ooc: Observed Order of Convergence.
                - re: Richardson Extrapolated value.
                - GCI: Grid Convergence Index (same units as QOI if default absolute GCI option used - see constructor)
                - error: A string indicating an error condition ('divergence' or 'oscillatory') or None.
        """  
        if not is_intermediate_triplet:
            self._reset()

        # Initialize return values
        ooc = None
        re = None
        gci = None
        error = None
    
        # Assign QOI values for each mesh
        q1 = qoi_values[0]
        q2 = qoi_values[1]
        q3 = qoi_values[2]
    
        # Check the convergence type using the triplet of QOI values
        conv_type = self._check_oscillatory_status(q1,q2,q3)
        if conv_type in [ConvergenceType.MONOTONIC_DIVERGENCE,ConvergenceType.OSCILLATORY_DIVERGENCE]:
            error = 'divergence'
            return ooc, re, gci, error
    
        if conv_type == ConvergenceType.OSCILLATORY_CONVERGENCE:
            error = 'oscillatory'
            return ooc, re, gci, error
    
        # Compute the ratios of consecutive h_values
        r21 = h_values[1]/h_values[0] 
        r32 = h_values[2]/h_values[1]
    
        # If the mesh ratios are nearly equal, use the direct formula
        if(np.abs(r21-r32)<1e-14): 
            r = r21
            e21 = q2-q1
            e32 = q3-q2
            ooc = np.log(np.abs(e32)/np.abs(e21))/np.log(r)
        else:
            # Define a function to solve for ooc when mesh ratios differ
            def fcn(p):
                return p*np.log(r21)+np.log(np.abs((q2-q1)/(q3-q2)))+np.log(np.abs((r32**p-1)/(r21**p-1)))
    
            # Check if the function fcn does not change sign over the interval p=0.1 to 5
            x = np.linspace(0.1,10,1000)
            y = fcn(x)
    
            if np.min(y)*np.max(y)>0:
                self._print("WARNING: when solving nonlinear function for OOC (non-constant r case), function may not cross zero for any value of p between 0.1 and 10")
                #plt.plot(x,y)
                #plt.plot(x,0*y,'r')
    
            # Estimate an initial guess for the observed order
            init_guess = np.log(np.abs((q3-q2)/(q2-q1)))/np.log(0.5*(r21+r32))
            # Use fsolve to find the root of fcn
            res = fsolve(fcn, init_guess)
            ooc = res[0]
            
    
        # constrain to be greater than 0.5 and less than formal order, if given
        constrained_ooc = self._compute_constrained_OOC(ooc, formal_order_conv, is_intermediate_triplet)
        
        # Compute the Richardson extrapolated value based on the found ooc
        re = q1 - (q2-q1)/(r21**constrained_ooc-1)

        gci = self._calculate_GCI(r21, q1, q2, ooc, constrained_ooc, formal_order_conv)
    
        if not is_intermediate_triplet:
            self._save_results(h_values, qoi_values, ooc, re, gci)

        return ooc, re, gci, error
    
    
 
        
    
    def analyze_largeN_mono_case(self, h_values, qoi_values, formal_order_conv = None):
        """
        Analyzes convergence metrics for cases of >3 mesh sizes.

        Only to be called with there is monotonic convergence on first triplet        
        Analyzes those three meshes to compute baseline metrics
        and then computes metrics for subsequent overlapping triplets. Results are stored in a DataFrame 
        
        Parameters:
            h_values (list or array-like): Mesh sizes (must be strictly increasing).
            qoi_values (list or array-like): QOI values for each mesh size.
            formal_order_conv (float, optional): Formal order of convergence.
        
        Returns:
            tuple: (ooc, re, GCI)
                - ooc: Observed Order of Convergence from the first three meshes.
                - re: Richardson Extrapolated value from the first three meshes.
                - GCI: Grid Convergence Index from the first three meshes.
        """
        self._reset()

        # Initialize output values
        ooc = None
        re = None
        gci = None
    
        # Check convergence status for the first three QOI values
        q1 = qoi_values[0]
        q2 = qoi_values[1]
        q3 = qoi_values[2]    
        conv_type = self._check_oscillatory_status(q1,q2,q3)
        assert(conv_type == ConvergenceType.MONOTONIC_CONVERGENCE)

        # Compute metrics for the first triplet (indices 0, 1, 2)
        ooc, re, gci, error = self.analyze_N3_case(h_values[0:3],qoi_values[0:3],formal_order_conv)
        # Assert that there is no error for the first triplet, since already checked for monotonic convergence
        assert(error == None)
    
        # Create an empty DataFrame to store convergence metrics for each triplet
        self.intermediate_triplet_metrics = pd.DataFrame(columns=['triplet', 'convergence', 'OOC', 'RE', 'GCI'])
    
        # Add the results for the first triplet to the DataFrame
        new_row = pd.DataFrame({'triplet': ["0,1,2"], 'convergence': ["converging (monotonic)"], 'OOC': [ooc], 'RE': [re], 'GCI': [gci]})

        ## concat leads to a FutureWarning so use .loc instead
        #self.intermediate_triplet_metrics = pd.concat([self.intermediate_triplet_metrics, new_row], ignore_index=True)
        self.intermediate_triplet_metrics.loc[len(self.intermediate_triplet_metrics)] = new_row.iloc[0]

        # Label the convergence type based on the error condition returned
        for i in range(1,len(h_values)-2):
            inter_ooc, inter_re, inter_GCI, inter_error = self.analyze_N3_case(h_values[i:i+3],qoi_values[i:i+3],formal_order_conv,is_intermediate_triplet = True)
            if inter_error == "divergence":
                comment = "diverging"
            elif inter_error == "oscillatory":
                comment = "converging (oscillatory)"
            else:
                comment = "converging (monotonic)"

            # Append results for the current triplet to the DataFrame
            new_row = pd.DataFrame({'triplet': [f"{i},{i+1},{i+2}"], 'convergence': [comment], 'OOC': [inter_ooc], 'RE': [inter_re], 'GCI': [inter_GCI]})
            
            ## concat leads to a FutureWarning so use .loc instead
            #self.intermediate_triplet_metrics = pd.concat([self.intermediate_triplet_metrics, new_row], ignore_index=True)
            self.intermediate_triplet_metrics.loc[len(self.intermediate_triplet_metrics)] = new_row.iloc[0]


        # Print the summary DataFrame
        self._print(self.intermediate_triplet_metrics)

        self._save_results(h_values, qoi_values, ooc, re, gci)

        return ooc, re, gci
    
    
    def analyze_using_least_squares_method(self, h_values, qoi_values, formal_order_conv = None):
        """
        Performs a least squares fit on the given mesh sizes and QOI values.
        
        This method fits the model: QOI = finf + alpha * h^p, where:
            - finf is the extrapolated value as h -> 0,
            - alpha is a scaling parameter,
            - p is the order of convergence.
        
        Parameters:
            h_values (list or array-like): Mesh sizes.
            qoi_values (list or array-like): QOI values for each mesh.
        
        Returns:
            tuple: (ooc, re, GCI)
                - ooc: Fitted order of convergence (p).
                - re: Extrapolated QOI value at h=0.
                - GCI: Grid Convergence Index from the first three meshes (same units as QOI if default absolute GCI option used - see constructor).
        """    
        self._reset()

        # Define the objective function to minimize (sum of squared residuals)
        def func(params):
            finf, alpha, p = params
            result = 0
            # Sum the squared differences between the actual and fitted QOI values
            for i in range(len(qoi_values)):
                # Minimize this equation:
                result += (qoi_values[i] - (finf + alpha * h_values[i]**p))**2
            return result
    
        # Initial guess for finf, alpha, and p
        initial_guess = [qoi_values[-1], -0.015, 1] # Initial guess for finf, alpha, and p
        # Minimize the objective function using BFGS method
        soln = minimize(func, initial_guess, method='BFGS', tol=1e-6,
                        options={'maxiter': 1e5, 'disp': True})
    
        # Unpack the solution: note that re corresponds to finf in the model
        re, alpha, ooc = soln.x
        
            
        # Create a set of h values for plotting the least squares fit curve
        hh = np.exp(np.linspace(np.log(h_values[0]), np.log(h_values[-1]), 50, endpoint=True))
        ls_fit_q = 0*hh
        # Compute the fitted QOI values for each h value in the curve
        for i in range(len(hh)):
            ls_fit_q[i] = re + alpha*hh[i]**ooc
        # Package the curve data in a dictionary
        self.ls_fit_curve = dict({'h':hh,'q':ls_fit_q})
        
        # constrain to be greater than 0.5 and less than formal order, if given
        constrained_ooc = self._compute_constrained_OOC(ooc, formal_order_conv, suppress_message=False, will_be_used_for_RE=False)

        gci = self._calculate_GCI(h_values[1]/h_values[0], qoi_values[0], qoi_values[1], ooc, constrained_ooc, formal_order_conv)

        self._save_results(h_values, qoi_values, ooc, re, gci)

        return ooc, re, gci



    
    def plot(self,ax=None):
        """
        Plots the convergence verification results.
        
        This function creates a semilogarithmic plot of QOI vs. mesh size (h), adds horizontal lines
        for the extrapolated value and GCI bounds (if available), and overlays a least squares fit curve if provided.
        """
        # Create a new figure and axis if none is providedif ax is None:

        if self.last_ooc == None:
            raise ValueError("Cannot plot as did not run successfully")

        if ax == None:
            fig, ax = plt.subplots(1,1)
        else:
            fig = ax.figure
        

        # Plot the QOI values versus h on a semilog x-axis
        ax.semilogx(self.last_h_values, self.last_qoi_values, marker='o', linestyle='-')
        # Draw a horizontal line for the Richardson extrapolated value
        ax.axhline(y=self.last_re, color='r', linestyle='-', label=f'Extrapolated value: {self.last_re:.4f}')
        ax.set_title(f'Convergence Plot (Observed convergence rate: {self.last_ooc:.2f})')
    
        if self.use_absolute_GCI:    
            ax.axhline(y=self.last_qoi_values[0]+self.last_gci, color='r', linestyle='--', label="Finest mesh QOI +/- GCI")
            ax.axhline(y=self.last_qoi_values[0]-self.last_gci, color='r', linestyle='--')
        else:
            ax.axhline(y=self.last_qoi_values[0]*(1+self.last_gci), color='r', linestyle='--', label="Finest mesh QOI * (1 +/- relativeGCI)")
            ax.axhline(y=self.last_qoi_values[0]*(1-self.last_gci), color='r', linestyle='--')
            

        assert(self.ls_fit_curve == None or self.intermediate_triplet_metrics == None)
        
        # If a least squares fit curve was computed, plot it on the same axis
        if self.ls_fit_curve is not None:
            ax.semilogx(self.ls_fit_curve['h'],self.ls_fit_curve['q'],'orange',label='least squares fit')
        
        # Set axis labels if provided, otherwise use default labels
        ax.set_xlabel(self.x_label)
        ax.set_ylabel('QOI')
    
        # Display the legend and show the plot
        ax.legend()
        plt.show()
        
        return fig, ax
