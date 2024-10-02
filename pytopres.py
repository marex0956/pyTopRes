import re, os
import argparse
import csv
import sys
import pandas as pd

def main():
    # Argparse added
    parser = argparse.ArgumentParser(
                    prog='pytopres',
                    description='Add topography coordinates in Res2DInv format .dat file. Indicated for lazy applied geophysicist.',
                    epilog='by Geol. Marco Re, Teglio Veneto, VE, ITALY')
    # Add argument coordinates: requires the path of a valid excel file, formatted as in the help section
    parser.add_argument("-c","--coordinates", default=["coordinates.xlsx"], 
                        help='''a .xlsx table with the followings columns:
                            fid;  name;  distance (between electrodes, in m); x; y; z. 
                            The order may vary and the decimal separator must be dot''' , type=str, nargs=1)
    # Add argument files: are the name of the files that you want to modify 
    parser.add_argument("-f","--files", help = 'files you want to add topography (*\\.dat if you want all .dat files)[mandatory]', nargs=r'*', type=str)
    # Add argument water: optional, if you have a bathymetry add the resistivity and chargeability of water layer
    parser.add_argument("-w","--water",help = "insert the water resistivity [arg1] and chargeability [arg2] if you want a water layer above topography [optional]", nargs=2, type=float)
    # Add argument limits: to modify only if you have a coastline at the extremities of the ert measurements
    parser.add_argument("-l","--limits",default=[-100, 200], help = "insert the water layer horizontal limits, e.g. distance from coastline if present [optional]", nargs=2, type=float )
    # A Namespace with all the arguments
    args = parser.parse_args()
    files = args.files
    water = args.water
    limits = args.limits   
    # Read excel file in coordinates argument
    try:
        topo = pd.read_excel(*args.coordinates)
    except ValueError:
        sys.exit("Missing coordinates file")
    # if no file arguments, pick all the dat files in current folder
    if args.files is None:
        files = []
        path = os.getcwd()
        dir_list = os.listdir(path)
        # append to a list all the files that ends with .dat
        for file in dir_list:
            if file.endswith('.dat'):
                files.append(file)
    
    # Check if files in args.files exists
    for file in files:
        try:
            with open(file, 'r') as dat:
                print("", end="")
        except (FileNotFoundError, TypeError):
                sys.exit(f"Missing file {file}")


    
# Find a match between each file and topography table 
    # Return a dictionary with the table name as keys and the file as values
    match = match_files(topo, files)
    # Check if --water exitsts, and build bathymetry lines with the arguments
    if args.water is None:
        bathymetry = 0
        # check if negative elevation is present and ask to insert new parameters
        if (topo['z']<0).any():
            warn = input("negative elevations but no bathymetry: continue or add --water arguments? ")
            if warn.strip().lower() == "continue" or warn.strip() == "":
                print("", end='')
            else:
                # add new resistivity and cheargeablility values
                ask = input("Do you want to change the water layer limits? ").strip()
                if ask != "" or ask.lower() != "no":
                    limits = ask.split()
                water = warn.split()
                try:
                    limits = [float(limits[0]), float(limits[1])]

                    water = [float(water[0]),float(water[1])]
                except:
                    sys.exit("Input a valid number")
                bathymetry = ['1',f'{water[0]} {water[1]}',f'{limits[0]} {limits[1]}','0','1','0','0','0']
    # if args.water is not null, add the parameters from command-line argument                                            
    else:
        bathymetry = ['1',f'{water[0]} {water[1]}',f'{limits[0]} {limits[1]}','0','1','0','0','0']
        

#Extract the part of coordinate table with the right name
    topo['number'] = topo['name'].str.extract(r'(\d+)').astype(int)
    grouped = topo.groupby('name')
    sorted_names = grouped['number'].min().sort_values().index
    #Starts a loop for each line and each unique name value in the coordinates table 
    for value in sorted_names:
        #Keeps only the names in match too
        for k, v in match.items():
            if value == k:
                # Reassemble only the required parts of table, sorted following the Res2DInv file format 
                vert, coord = read_topo(topo, value)
                print(vert,coord)
                # Write the topography in a temporary csv file and than in the actual .dat file
                msg = write_topo(v, vert, coord, bathymetry)
                print(msg)


def match_files(topo, files):
    # Group a dataframe by name (ERT1, ERT2 etc.)
    grouped_df = topo.groupby('name')
    # Empty dictionaries
    match_dict = {}
    xdict = {}
    # for each file in files append as keys the associated numbers inside name
    for file in files:
        match2 = re.search(r'\d{1,2}', file)
        match_dict[match2.group(0)] = file
    # find a match between the match dictionary and value    
    for value, data in grouped_df:
        match = re.search(r'\d{1,2}', value)
        if match.group(0) in match_dict.keys():
            xdict[value] = match_dict[match.group(0)]
    # return a dictionary {'ERT1':'ert1...','ERT2':'ert2...'}
    return xdict
     

def read_topo(topo, value):
    # Writes a table 'ert' with only the right name values
    ert = topo[topo['name'] == value]
    # Scrapes only the right columns from ert
    #'coord' is for the global coordinates
    coord = ert[['distance','x','y']]
    #'vert' is for the vertical topography/bathymetry
    vert = ert[['distance','z']]
    # The first row is the interelectrode distance, that is the 2nd row in the column 'distance' 
    row1 = pd.DataFrame([[2,'']], columns=['distance','z'])
    # The 2nd row is the number of points in the column
    row2 = pd.DataFrame([[len(vert),'']], columns=['distance','z'])
    #'vert' must terminate with a flag 1 if we also have global coordinates
    end = pd.DataFrame([[1,'']], columns=['distance','z'])
    # Concatenates all the new lines
    vert = pd.concat([row1,row2,vert,end], ignore_index=True)
    # The header of global coordinates, that are the following 4 rows
    row_1 = pd.DataFrame([['Global Coordinates present','','']], columns=['distance','x','y'])
    row_2 = pd.DataFrame([['Number of coordinate points','','']], columns=['distance','x','y'])
    row_3 = pd.DataFrame([[len(coord),'','']], columns=['distance','x','y'])
    row_4 = pd.DataFrame([['Local', 'Longitude', 'Latitude']], columns=['distance','x','y'])
    # The end of the file must contain at least 3 zeros
    end2 = pd.DataFrame([['0', '', '']], columns=['distance','x','y'])
    coord = pd.concat([row_1,row_2,row_3,row_4,coord,end2,end2,end2], ignore_index=True)
    # Returns the lines to add to .dat files
    return vert, coord

# Opens the .dat files, writes the content in a temporary csv with the same name, check 
def write_topo(file,vert,coord, bathymetry):    
    # split file in the actual file name and in his extension
    file_name , ext = file.split('.')
    # check if there is a file, if not skip the missing file
    try:
        #put the content of the file in a list
        datContent = [i.strip().split() for i in open(file).readlines()]
    except (FileNotFoundError):
        print(f'File {file} not found')
    # create a new csv file with the right name
    with open(file_name + ".csv", 'w', newline='') as out_file:
        writer = csv.writer(out_file)
        writer.writerows(datContent)
    # read the right number of lines to keep, using the number of measurement (4th line in dat file) + 9 lines of header
    with open(file_name + ".csv", 'r') as f:
        lines = f.readlines()
        # check if the 4th line of the .dat file contains a number
        try:
            fourth_line_value = float(lines[3].strip())  
            num_lines_to_keep = int(fourth_line_value) + 9
            lines = lines[:num_lines_to_keep]
        except (IndexError, ValueError):
            sys.exit("The 4th line of the .dat file must contain an integer value.")
    # write the lines to keep from the dat file
    with open(file_name + ".csv", 'w') as f:
            f.writelines(lines)
    # add the 'vert' table to the csv temporary file 
    vert.to_csv(file_name + ".csv", mode='a', index=False, header=False)
    # add the 'coord' table to the csv temporary file
    coord.to_csv(file_name + ".csv", mode='a', index=False, header=False)
    if bathymetry != 0:
        with open(file_name + ".csv", "r") as csv_read:
                lines = csv_read.readlines()
                # Insert new lines above the second to last line
                lines.insert(-2, "\n".join(bathymetry) + "\n")
        # Write new lines from bathimetry
        with open(file_name + ".csv", "w") as csv_write:
                csv_write.writelines(lines)
    # convert the csv in .dat
    with open(file_name + ".csv", 'r') as csv_file, open(file_name + "_topo.dat", 'w') as dat_file:
        for line in csv_file:
            dat_file.write(line.replace(',', '\t'))
    # remove the csv files
    os.remove(file_name + ".csv")
    # Send a comforting message
    return f'{file}: done'

if __name__ == "__main__":
    main()
