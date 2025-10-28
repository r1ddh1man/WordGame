import random
try:
    len_check=True
    while (len_check):
        N = int(input("How many letters do you want to play with?"))
        fs=open('words.txt','r')
        lines = fs.readlines()[0].replace('\n','')
        newlin=lines.split(' ')
        fs.close()
        final_list=[]
        for i in range(999):
        	if len(newlin[i])==N:
        		final_list.append(newlin[i])
        len_check = False
        if N<=0:
            print("Please enter a positive integer")
            len_check = True
except ValueError:
    print("Please enter a positive integer")
else:
	trial=0
	alphabets = [chr(i) for i in range(97,123)]
	right_len=1
	choice = final_list[random.randint(0,len(final_list)-1)]
	while (right_len==1):
		guess = input('Your guess:')
		if len(guess)!=N:
			print("Please check the number of letters in your word")
		else:
			guess_dict= {alphabets[i]:0 for i in range(26)}
			for i in guess.lower():
					guess_dict[i]=1
			choice_dict = {alphabets[i]:0 for i in range(26)}
			for j in choice.lower():
					choice_dict[j]=1
			n=0
			if (guess.lower()==choice.lower()):
				print("Congratulations! Your guess,",guess.upper(),",is correct.")
				right_len = 0
			else:
				for i in range(26):
					if (choice_dict[list(choice_dict.keys())[i]]==guess_dict[list(guess_dict.keys())[i]] and \
					guess_dict[list(guess_dict.keys())[i]]!=0):
						n+=1
				print("Your guess has",n,"letters in common with my chosen word.")
				trial+=1	
				if trial>=20:
					print("Sorry you ran out of turns :( The word is ",choice)
					break