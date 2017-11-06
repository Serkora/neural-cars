def det(m):
	if len(m) != len(m[0]):
		raise ValueError("Matrix must be square!")
	
	elif len(m) == 2:
		return m[0][0] * m[1][1] - m[0][1] * m[1][0]
	else:
		ret = 0
		neg = True
		for i in range(len(m)):
			minor = [row[0:i] + row[i+1:] for row in m[1:]]
			val = m[0][i] * det(minor)
			if neg:
				ret -= val
			else:
				ret += val
			neg = not neg
		return ret
			
