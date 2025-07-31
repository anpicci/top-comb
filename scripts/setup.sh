# Scripts for setting up the environment

# Set of colors for prompts

function custom_msg() {
	ERROR="\e[31m" # red
	GOOD="\e[32m" # green 
	INFO="\e[34m" # blue
	WARN="\e[93m" # yellow
	ENDCOLOR="\e[0m"

	MSG_TYPE=$1
	case $MSG_TYPE in
		ERROR) COLOR=$ERROR;;
		GOOD) COLOR=$GOOD;;
		INFO) COLOR=$INFO;;
		WARN) COLOR=$WARN;;
		*) COLOR=$ENDCOLOR;;
	esac
	MSG=$2

	echo -e " >> ${COLOR} ${MSG} ${ENDCOLOR}"
}

function quit_setup() {
	custom_msg WARN "Quitting setup script..."
	exit 0
}

function check_module() {
	# Check the module has been installed
	isInit=$(git submodule status | grep $1)
	case $isInit in
		\-*)
	 		custom_msg ERROR "$1 is not initialized. Would you like to initialize it?"
			select ans in yes no; do
				case $ans in
					yes)
						git submodule update --init $1
						break
						;;
					no)
						quit_setup
						;;
				esac
			done
			;;
		U.*)
			custom_msg WARN "$1 is initialized, but please be aware" 
			custom_msg WARN "are merging conflicts with the revision used in the main repository"
			;;
		*)
			custom_msg GOOD "$1 module is properly initialized and up to date"
			;;
	esac
}

function setup_genproductions() {
	custom_msg INFO "Setting up environment for gridpack production"
	custom_msg NC "This is based in the Genproductions framework."

	check_module "genproductions_scripts"	
	check_module "topcomb_smeft_cards"
	
}

function setup_cmgrdf() {
	custom_msg INFO "Setting up environment for reinterpretation"
	custom_msg NC "This is based in the CMGRDF framework."

	
	check_module "cmgrdf-prototype"	

	# Now do the basic setup
	source /cvmfs/sft.cern.ch/lcg/views/dev3/latest/x86_64-el9-gcc13-opt/setup.sh
	pushd cmgrdf-prototype
	git submodule update --init externals/RoccoR 
	make -j 4
	popd
	
}

# Print a welcome message
custom_msg GOOD "Running the setup for the EFT combination"
custom_msg NC "Please select which step of the setup you would like to run: "

select mode in  Gridpack Reinterpretation Quit; do
	case $mode in
		Gridpack)
			setup_genproductions
			break
			;;

		Reinterpretation)
			setup_cmgrdf
			break
			;;
		Quit)
			quit_setup	
			break
			;;
	esac
done


