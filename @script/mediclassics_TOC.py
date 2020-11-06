import os, re, shutil, time
"""
유의사항
- 동의보감의 '내경편 권1'이나 의학입문의 '권수상, 권우2상'과 같은 경우는 수작업으로 다시 정렬해야 합니다.
- DB 문법의 키-밸류 형태 외에 별도의 밸리데이션 절차는 없습니다. 즉, 협업시스템의 뷰어 변환을 거친 파일만 정상적으로 처리됩니다.
- url 링크는 몇가지 문제가 있어서 넣지 못했습니다. 협업시스템 '파일백업' 기능을 수정한 후에 보완할 예정입니다.
- 서적별 병합파일이나 중간 파일을 사용하려면 'shutil.rmtree( f'{tempDir}' )'을 주석 처리하면 됩니다.
"""
#########################################
cwd = os.path.dirname(os.path.realpath(__file__))
#cwd = "D:/test/mediclassics_text_backup" #아톰 실행용
#########################################

# 경로 구분자 전처리
cwd = os.getcwd().replace("\\", "/")
if cwd[-1] == "/":
	cwd = cwd[:-1]

# 작업용 임시 폴더 만들기 (작업 후 삭제)
tempDir = f'{cwd}/temp'
if not os.path.isdir( tempDir ):
	os.mkdir( tempDir )
else:
	shutil.rmtree( f'{tempDir}' )
	os.mkdir( tempDir )

# 결과물 폴더 만들기
TOCDir = f'{cwd}/mediclassicsTOC'
if not os.path.isdir( TOCDir ):
	os.mkdir( TOCDir )
else:
	shutil.rmtree( f'{TOCDir}' )
	os.mkdir( TOCDir )

# 로그 폴더 만들기
errorDir = f'{cwd}/log'
if not os.path.isdir( errorDir ):
	os.mkdir( errorDir )
else:
	shutil.rmtree( f'{errorDir}' )
	os.mkdir( errorDir )


def extractTOC():
	volumeToBook() # 서적별로 폴더 만든 후 작업용으로 1벌 복사
	orderFileName() # 권 숫자 정렬
	deleteMetadata() # 주석 및 의미분류 삭제
	addOutlineNum() # 권별파일 상태에서 개요번호 작성
	addContentsID() # 권별파일 상태에서 콘텐츠번호 작성
	mergeVolumes() # 서적별로 모든 권을 하나의 파일로 병합
	TOCformatting() # 병합된 파일에서 불필요한 부분을 삭제하고 정해진 양식으로 파일에 목차를 작성
	TOCformattingYAML() # 얌 형식으로 목차 작성

	time.sleep( 1 ) # 컴퓨터에서 파일 처리시간 여유

	# 서적별 병합파일이나 중간 파일을 사용하려면 아래줄을 주석 처리
	shutil.rmtree( f'{tempDir}' ) # 추출이 끝난 후 작업용 폴더 통째로 삭제

	print( "모든 작업이 완료되었습니다.\n5초 후에 창이 닫힙니다......" )
	time.sleep( 5 )


def volumeToBook():
	for file in os.listdir( cwd ):
		if file.endswith(".txt"):
			# 폴더 내 파일명에서 처음 언더바 전까지 자른 후 서적명으로 폴더 만들기
			bookName = re.sub( r"^([^_]+?)_.+?$", r"\1", file )
			bookDir = f'{tempDir}/{bookName}'
			if not os.path.isdir( bookDir ):
				os.mkdir( bookDir )

			# 서적명 폴더로 파일 복사
			shutil.copy( f'{cwd}/{file}', f'{bookDir}' )
			print( f'(copy files) {file}' )


def orderFileName():
	for bookName in os.listdir( tempDir ): #서적 폴더 마다
		for volumeName in os.listdir( f'{tempDir}/{bookName}' ): #권 파일 마다
			try:
				volumeName1 = re.sub( r"^([^\d]+?)(\d{1,3})([^\d]*?)$", r"\1", volumeName )
				volumeName2 = re.sub( r"^([^\d]+?)(\d{1,3})([^\d]*?)$", r"\2", volumeName )
				volumeName3 = re.sub( r"^([^\d]+?)(\d{1,3})([^\d]*?)$", r"\3", volumeName )
				volumeName2 = f'{int(volumeName2):03d}'
				volumeNameNew = f'{volumeName1}{volumeName2}{volumeName3}'
				os.rename( f'{tempDir}/{bookName}/{volumeName}', f'{tempDir}/{bookName}/{volumeNameNew}' )
			except:
				pass

		print( f'(rename files by order) {bookName}' )


def deleteMetadata():
	for bookName in os.listdir( tempDir ):
		for volumeName in os.listdir( f'{tempDir}/{bookName}' ):
			if volumeName.endswith( ".txt" ) and os.path.getsize( f'{tempDir}/{bookName}/{volumeName}' ) > 0:
				inputDataObj = open( f'{tempDir}/{bookName}/{volumeName}', 'r', encoding="utf-8" )
				inputData = inputDataObj.read()

				patterns = [
					(r"\r\n", r"\n"), #  \r 삭제
					(r"^//.+?$\n*", r""), #  주석 삭제
					(r"//.*?$", r""), #  주석 삭제2
					(r"^\[.+?$\n*", r""), #  의미분류 삭제
					(r"^[ ]+?$", r""), #  빈 줄의 공백 삭제
					(r"\n{2,}", r"\n\n"), #  개행 3줄 이상을 2줄로
					]

				for ( before, after ) in patterns:
					inputData = re.sub( before, after, inputData, flags=re.MULTILINE )
				modifiedData = inputData.strip() #파일 내 앞뒤 공백 삭제

				with open( f'{tempDir}/{bookName}/{volumeName}', "w", encoding="utf-8" ) as output:
					output.write( modifiedData )

		print( f'(delete non-contents) {bookName}' )


def addContentsID():
	for bookName in os.listdir( tempDir ):
		volumeIndex = 1
		for volumeName in os.listdir( f'{tempDir}/{bookName}' ):
			if volumeName.endswith( ".txt" ) and os.path.getsize( f'{tempDir}/{bookName}/{volumeName}' ) > 0:
				inputDataObj = open( f'{tempDir}/{bookName}/{volumeName}', 'r', encoding="utf-8" )
				inputData = inputDataObj.read()

				volumeAll = []
				paragraphList = inputData.split( "\n\n" ) #권을 문단 단위로 쪼개기
				for ( idx, x ) in enumerate( paragraphList ):
					#Vol Name은 권차, Contents ID는 콘텐츠 번호
					paragraphOne = f'((VN))\t{volumeIndex}\n((CI))\t{idx+1}\n{x}'
					volumeAll.append( paragraphOne )

				with open( f'{tempDir}/{bookName}/{volumeName}', "w", encoding="utf-8" ) as output:
					output.write( "\n\n".join( volumeAll ) )
				volumeIndex = volumeIndex + 1

		print( f'(add contents ID) {bookName}' )


def addOutlineNum():
	errorReport = []
	for bookName in os.listdir( tempDir ):
		for volumeName in os.listdir( f'{tempDir}/{bookName}' ):
			if volumeName.endswith( ".txt" ):
				if not os.path.getsize( f'{tempDir}/{bookName}/{volumeName}' ) == 0: # 유효한 파일만
					volumeOne = []
					inputDataObj = open( f'{tempDir}/{bookName}/{volumeName}', 'r', encoding="utf-8" )
					inputData = inputDataObj.read()
					paragraphList = inputData.split( "\n\n" ) #문단 단위로 나누기

					# 개요번호 각 자리에 해당하는 초기값
					BB = ""
					CC = ""
					DD = ""
					EE = ""
					FF = ""

					for x in paragraphList: #문단
						if re.findall( r"\(\(LV\)\)\t[AOZSXYPT][AOZSXYPT\d]", x ): #개요번호 안붙이는 거
							outlineNum = f'((ON))\tnull' # 포매팅 : BB-FF 이외에는 null로 표시
							volumeOne.append( f'{outlineNum}\n{x}' )

						else:
							if re.findall( r"\tB[B-P]", x ): # BB 문단이 나왔을 때
								if BB == "": # 처음이면
									BB = 1
								else: # 처음이 아니라면
									BB = BB + 1 # BB 자리에 1을 더하고
									CC = "" # 나머지는 초기화
									DD = ""
									EE = ""
									FF = ""
							elif re.findall( r"\tC[C-P]", x ):
								if CC == "":
									CC = 1
								else:
									CC = CC + 1
									DD = ""
									EE = ""
									FF = ""
							elif re.findall( r"\tD[D-P]", x ):
								if DD == "":
									DD = 1
								else:
									DD = DD + 1
									EE = ""
									FF = ""
							elif re.findall( r"\tE[E-P]", x ):
								if EE == "":
									EE = 1
								else:
									EE = EE + 1
									FF = ""
							elif re.findall( r"\tF[F-P]", x ):
								if FF == "":
									FF = 1
								else:
									FF = FF + 1
							else: # 수준기호 맞지 않는 경우는 에러 리포트 파일에 추가
								volumeOne.append( f'((ON))\tDB 문법 에러\n{x}' ) # 텍스트 파일의 개요번호 자리에는 'DB 문법 에러'라고 기록
								print( f'(DB 문법 에러)---------------{volumeName}')
								errorOne = f'▶DB 문법 에러 : {bookName} > {volumeName}\n{x}\n\n' # 에러 리포트 파일에도 기록
								errorReport.append(errorOne)

							outlineNum = f'((ON))\t{BB}.{CC}.{DD}.{EE}.{FF}' # 포매팅 : 유효한 개요번호
							volumeOne.append( f'{outlineNum}\n{x}' )


					outputData = "\n\n".join( volumeOne ) # 문단을 다시 권단위로 합침
					outputData = re.sub( r"(\(\(ON\)\)\t.*?[\d]+?)[.]+?$", r"\1", outputData, flags=re.MULTILINE ) # 개요번호에서 유효하지 않은 마침표 삭제
					outputData = re.sub( r"\n{2,}", r"\n\n", outputData )

					with open( f'{tempDir}/{bookName}/{volumeName}', "w", encoding="utf-8" ) as output:
						output.write( outputData )

				else: # 유효하지 않은 파일은 에러 리포트 : 빈 파일, DB 형식 아닌 파일
					print( f'뭔가 이상한 파일이 있어요---------------{volumeName}' )
					errorOne = f'▶파일 내용 확인 필요 : {bookName} > {volumeName}\n\n'
					errorReport.append( errorOne )


		print( f'(add outline number) {bookName}' )

	# 에러 리포트 파일 쓰기
	with open( f'{errorDir}/error-report.txt', "w", encoding="utf-8" ) as output:
		output.write( "\n".join( errorReport ) )


def mergeVolumes(): # 권 단위의 파일을 서적 단위로 합침
	for bookName in os.listdir( tempDir ):
		bookAll = []
		for volumeName in os.listdir( f'{tempDir}/{bookName}' ):
			if volumeName.endswith( ".txt" ):
				if not os.path.getsize( f'{tempDir}/{bookName}/{volumeName}' ) == 0:
					inputDataObj = open( f'{tempDir}/{bookName}/{volumeName}', 'r', encoding="utf-8" )
					inputData = inputDataObj.read()
					bookAll.append( inputData + "\n\n" )

		outputData = "\n".join( bookAll )
		outputData = re.sub( r"\n{2,}", r"\n\n", outputData )
		with open( f'{tempDir}/{bookName}/bookALL.txt', "w", encoding="utf-8" ) as output:
			output.write( outputData )

		print( f'(concatnate files by book) {bookName}' )


def TOCformatting(): # 서적 단위로 합친 파일에서 목차 추출
	for bookName in os.listdir( tempDir ):
		inputDataObj = open( f'{tempDir}/{bookName}/bookALL.txt', 'r', encoding="utf-8" )
		inputData = inputDataObj.read()

		patterns = [
			(r"\r\n", r"\n"), #  \r 삭제
			(r"^\(\(LV\)\)\t([ABCO\d]{2})$\r*\n\(\(OR\)\)\t(.+?)$", r"\1\t\2"), # 1줄 형식 + 원문만
			(r"^\(.+?$", r""), # AA, BB, CC, OO이외에는 모두 삭제
			(r"\[[smng]{2}/[^]]+?\]", r""), # sm, ps, ng 삭제
			(r"\[ip/([^]]+?)\]", r"\1"), # ip 삭제
			(r"\{([^}]*?)[:=][^}]+?\}", r"\1"), # 주석은 대상 글자만 남기고 삭제
			(r"\n{2,}", r"\n"), #  3줄 이상을 2줄로
			(r"^AA\t", r"\n□ "), #  AA 포매팅
			(r"^[BO].\t", r"  - "), #  BB, OO 포매팅
			(r"^C.\t", r"    ㆍ "), #  CC 포매팅
			]

		for ( before, after ) in patterns:
			inputData = re.sub( before, after, inputData, flags=re.MULTILINE )
		inputData = inputData.strip() #파일 내 앞뒤 공백 삭제

		bookDir = f'{TOCDir}/{bookName}'
		if not os.path.isdir( bookDir ): # 서적명으로 폴더 만들기
			os.mkdir( bookDir )

		# 3수준 목차 파일 쓰기
		with open( f'{bookDir}/{bookName}_TOC_3step.txt', "w", encoding="utf-8" ) as output:
			output.write( inputData )

		# 2수준 목차 파일 쓰기 : 3수준 목차의 CC 부분 삭제
		inputData = re.sub( r"^    ㆍ .+?$\r*\n", r"", inputData, flags=re.MULTILINE )
		inputData = re.sub( r"^    ㆍ .+?$", r"", inputData, flags=re.MULTILINE )
		with open( f'{bookDir}/{bookName}_TOC_2step.txt', "w", encoding="utf-8" ) as output:
			output.write( inputData )

		print( f'(extract TOC) {bookName}' )


def TOCformattingYAML(): # 권 단위 파일에서 목차 정보 추출
	bookNum = 1 # 서적 ID용
	for bookName in os.listdir( tempDir ):
		bookALL = [ f'bookID: {bookNum}\ncontentsLinkBookID: \nbookName: "{bookName}"\nvolumes:' ]
		volumeNum = 1 # 권 ID 용
		for volumeName in os.listdir( f'{tempDir}/{bookName}' ):
			volumeALL = [ f'  - vol_{volumeNum}:']
			if volumeName.endswith( ".txt" ) and not volumeName == "bookALL.txt":
				if not os.path.getsize( f'{tempDir}/{bookName}/{volumeName}' ) == 0: # 유효한 파일만
					inputDataObj = open( f'{tempDir}/{bookName}/{volumeName}', 'r', encoding="utf-8" )
					inputData = inputDataObj.read()
					inputData = inputData.split( "\n\n" ) # 문단단위로 쪼개기

					i = 1 # yaml 목차용 시리얼 ID
					for p in inputData:
						if not re.findall( r"\(\(LV\)\)\t[ZSXYPT].", p ): # 제목 이외 수준기호는 제외
							volumeALL.append( f'((ID))\t{i}\n{p}' )
							i = i + 1

				else:
					volumeALL.append( "" )

				volumeALL = "\n".join( volumeALL )

				patterns = [
					(r"\r\n", r"\n"), #  \r 삭제
					(r'"', r'″'), #  "를 특수기호로 처리
					(r"\(\(VN\)\)\t.+?$\r*\n", r""), # VN 삭제
					(r"^\(\((..)\)\)\t", r"      \1: "), # 키-밸류 형식으로 변경
					(r"    ID\:", r"  - ID:"), # ID 앞에 어레이 표시
					(r'ON\: (.+?)$', r'outlineNum: "\1"'), # outlineNum
					(r'CI\: (.+?)$', r'contentsLinkID: \1'), # contentsLinkID
					(r'LV\: (.+?)$', r'LV: "\1"'), # LV
					(r'OR\: (.+?)$', r'OR: "\1"'), # OR
					(r'AK\: (.+?)$', r'AK: "\1"'), # AK 옛한글
					(r'KO\: (.+?)$', r'KO: "\1"'), # KO
					(r'EN\: (.+?)$', r'EN: "\1"'), # EN
					(r'AN\: (.+?)$', r'AN: "\1"'), # AN 주해
					(r"\n{2,}", r"\n"), #  3줄 이상을 2줄로
					]

				for ( before, after ) in patterns:
					volumeALL = re.sub( before, after, volumeALL, flags=re.MULTILINE )

				bookALL.append( volumeALL )

				volumeNum = volumeNum + 1

		bookALL = "\n".join( bookALL )

		bookDir = f'{TOCDir}/{bookName}'
		if not os.path.isdir( bookDir ): # 서적 폴더가 없으면 만들기
			os.mkdir( bookDir )

		with open( f'{bookDir}/{bookName}_TOC_yaml.yml', "w", encoding="utf-8" ) as output:
			output.write( bookALL )

		print( f'(convert TOC to yaml) {bookName}' )

		bookNum = bookNum + 1


extractTOC()
