#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
	Serveur Python Temps Réel pour l'Echange de Pokemon (SpyTREP)
	
	Version :
		0.4.0 (25 mais 2013)

	Auteur :
		daarkmoon@mailoo.org

	A propos :
		Il s'agit d'une alternative en python du script php de Sphinx permettant de
		créer un serveur d'échange temps réel pour Pokemon Script Project.
		(http://pokemonscriptproject.xooit.fr/t10279-Echanges-en-temps-reel-v2-0.htm?theme=test)
		Alternative réaliser avec l'aimable autorisation de Sphinx, merci à lui.

	License :
		Ce programe est distribué sous license : 
			"LICENCE BEERWARE" (Révision 42):
				daarkmoon@mailoo.org a créé ce fichier. Tant que vous conservez cet avertissement,
				vous pouvez faire ce que vous voulez de ce truc. Si on se rencontre un jour et
				que vous pensez que ce truc vaut le coup, vous pouvez me payer une bière en retour.

	Dépendance :
		Ce programe utilise les bibliothéques suivantes :
			- Twisted (https://twistedmatrix.com)
			  sous License MIT (http://opensource.org/licenses/mit-license.php)
			- Zope.interface (http://pypi.python.org/pypi/zope.interface)
			  sous License ZPL 2.1 (http://old.zope.org/Resources/License/ZPL-2.1)
'''

# Chargement des librairies dont twisted sert pour émuler un serveur web
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor
import time
import logging
import logging.config
import os
import random
import sys

class Player:
	'''
		Classe Player
			Description :
				Stock toute les infos sur le joueur dans une classe et non dans une
				multitude de fichier comme le faisait le script php

			Liste des attributs :			
				ID			: ID du Joueur
				name		: Nom du Joueur
				last_seen	: Dernière présence enregister
				pkm  		: Pokemon envoyé (version crypté)
				friend		: ID du joueur avec qui on échange
				ech			: Jeton/Timestamp pour l'échange 
				ok			: Jeton/Timestamp pour la validation
				ca			: Jeton/Timestamp pour l'annulation
				syn			: Jeton/Timestamp pour la syncronisation

			Liste des méthodes :
				__init__(Code)		: Créé un joueur depuis le Code (le code se présent sous la forme ID_Pseudo)
				__repr__()			: Formatage de la classage joueur pour impression
				seen()				: Actualise le la présence du joueur
				set_ech()			: Actualise le Jeton/Timestamp pour l'échange
				set_ok()			: Actualise le Jeton/Timestamp pour la validation
				set_ca()			: Actualise le Jeton/Timestamp pour l'annulation
				set_syn()			: Actualise le Jeton/Timestamp pour la syncronisation
				reset_all()			: Remettre à 0 les Jeton/Timestamp
	'''
	
	def __init__ (self,code):			
		self.id, self.name = code.split("_",1)
		self.last_seen = time.time()
		self.pkm = ""
		self.friend = ""
		self.ech = 0
		self.ok  = 0
		self.ca  = 0
		self.syn = 0
	
	def __repr__(self):
		'''Formatage de la classage joueur pour impression'''
		return self.name + " (" + self.id + ")"
		
	def seen (self):
		'''Actualise la présence du joueur'''
		self.last_seen = time.time()

	def set_ech (self):
		'''Actualise le Jeton/Timestamp pour l'échange'''
		self.ech = time.time()
		
	def set_ok (self):
		'''Actualise le Jeton/Timestamp pour la validation'''
		self.ok = time.time()
		
	def set_ca (self):
		'''Actualise le Jeton/Timestamp pour l'annulation'''
		self.ca = time.time()
		
	def set_syn (self):
		'''Actualise le Jeton/Timestamp pour la syncronisation'''
		self.syn = time.time ()
	
	def reset_all (self):
		'''Remets à 0 les Jeton/Timestamp'''
		self.pkm = ""		
		self.friend = ""
		self.ech = 0
		self.ok = 0
		self.ca = 0
		self.syn = 0

	
class Serveur(Resource):
	'''
		Classe Serveur
			Description :
				Emule le serveur d'échange en répondant au requette POST en HTTP
				Répond à requette GET pour indiquer l'état du serveur et lister les joueurs
			
			Liste des attributs :			
				timeout		: temps avant de considérer une conection comme perdu
				player list	: Dico des joueurs conecter (clefs = string de la forme "ID_pseudo", valeurs = objets de type player)
				
			Liste des méthodes :
				__init__(timeout=60)	: initialise le serrveur avec un timeout (par défaut 60 secondes)
				update()				: mets à jour la liste de joueur conectés
				render_GET(request)		: génére une réponse aux requettes GET (ignore l'argument request)
				render_POST(request)	: génére une réponse aux requettes POST
				
			Liste des variables :
				allows_modes 	: set des modes autorisés
				
			A faire :
				System de shutdown UID pour fermer proprement le serveur
				Page Admin pour vue complete + kick ?
				Ban list (DOS et requette mal fomé)
	'''
	
	def __init__ (self,timeout=60,log_conf='log.cfg',checkAuto=False,masterCode='{0:x}'.format(random.getrandbits(64))):
		'''initialise le serveur'''
		self.timeout = timeout
		self.checkAuto = checkAuto
		self.masterCode = masterCode
		self.player_list = {}
		self.logger = self.init_logger(log_conf)
		self.logger.info("Serveur Lance")
		self.logger.debug("Timeout serveur de %s secondes", timeout)
		self.logger.debug("L'interdiction des auto-echanges est regle sur  %s", str(checkAuto))
		self.logger.critical("Master Code : %s",self.masterCode)
		
	def init_logger(self,log_conf):
		if os.access(log_conf,os.F_OK):
			logging.config.fileConfig(log_conf) 
			logger = logging.getLogger()
			logger.debug("Chargement de la configuration du log")
		else:
			try:
				cfg = open(log_conf,'w')
			except IOError:
				logger = logging.getLogger()
				logger.setLevel(logging.DEBUG) 														# <- ajout config.txt
				formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
				fileHandler = logging.FileHandler('SPyTREP.log')												# <- ajout config.txt
				fileHandler.setLevel(logging.INFO)
				fileHandler.setFormatter(formatter)
				logger.addHandler(fileHandler)
				consoleHandler = logging.StreamHandler()
				consoleHandler.setLevel(logging.INFO)												# <- ajout config.txt
				logger.addHandler(consoleHandler)
				logger.warning("Impossible d'ecrire le fichier de configuration du log. Chargement de la version Hard-coder")
				return logger		
			
			# Crétion du fichier de config (coder très salement :/ )
			cfg.write("[loggers]\nkeys=root\n\n[handlers]\nkeys=consoleHandler,fileHandler\n\n[formatters]\nkeys=simpleFormatter\n\n[logger_root]\nlevel=DEBUG\nhandlers=consoleHandler,fileHandler\n\n[handler_consoleHandler]\nclass=StreamHandler\nlevel=INFO\nargs=(sys.stdout,)\n\n[handler_fileHandler]\nclass=FileHandler\nlevel=INFO\nformatter=simpleFormatter\nargs=('SPyTREP.log', 'a')\n\n[formatter_simpleFormatter]\nformat=%(asctime)s %(levelname)-8s %(message)s\n")
			cfg.close()
			logging.config.fileConfig(log_conf) 
			logger = logging.getLogger()
			logger.warning("Le fichier de configuration du log n'existe pas. Creation de ce dernier")
		return logger

	def update(self):
		'''Mets à jour la liste des joueurs présents'''
		self.logger.debug('Mise a jour de la liste de joueurs')
		for (code, player) in self.player_list.items():
			if time.time() - player.last_seen > self.timeout:
				self.logger.warning("Timeout de %s",player)
				del self.player_list[code]
		return
		
	def render_GET(self, request):
		'''
			Génére une réponse aux requettes GET (ignore l'argument request)
			
			La réponse se présente sous la forme d'une page HTML comprenant un tableau avec
			la liste des joueurs présent, leur ID et la date de la dernière requette reçu
			
			Si la requete comporte les arguments nessaire la page d'amin s'affiche
		'''	
		self.logger.debug("Requette GET recue : %s", request.args)
		
		# Mise à jour des joueurs présent à chaque requettes reçus
		self.update()
		
		# mode admin (warning si faux code)
		admin = False
		if 'mode' in request.args.keys() and request.args['mode'][0]=='admin':
			if 'code' in request.args.keys() and request.args['code'][0]==self.masterCode:
				admin = True
				self.logger.info("Connection a la page admin", request.args)
			else:
				self.logger.warning("Tentative de connection a la page admin echoue", request.args)
		
		# Mise en forme de la page principale
		text = 	"<!DOCTYPE html>\n"
		text +=	"  <html>\n"
		text +=	"    <head>\n"
		if admin:
			text +=	"      <title>Page d'administraion du Serveur d'&eacutechange Pokemon gemme</title>\n"
		else:
			text +=	"      <title>Serveur d'&eacutechange Pokemon gemme</title>\n"
		text +=	"    </head>\n"
		text +=	"    <body>\n"
		text +=	"      <center>\n"
		text +=	"        <h1>Le serveur d'&eacutechange pokemon gemme tourne</h1>\n"
		if len(self.player_list)==0:
			text +=	"          Aucun joueurs connect&eacutes\n"
		else:
			text +=	"        <table>\n"
			text +=	"          <caption>Joueurs connect&eacutes</caption>\n"
			text +=	"          <tr>\n"
			text +=	"            <th>Pseudo(ID)</th>\n"
			if admin:
				text +=	"            <th>Seen</th>\n"
				text +=	"            <th>Friend</th>\n"
				text +=	"            <th>Ech</th>\n"
				text +=	"            <th>ok</th>\n"
				text +=	"            <th>ca</th>\n"
				text +=	"            <th>syn</th>\n"
			text +=	"          </tr>\n"
			for player in self.player_list.values():
				text +=	"          <tr>\n"
				text +=	"            <td>"+str(player)+"</td>\n"
				if admin:
					text +=	"            <td>"+str(player.last_seen)+"</td>\n" #amélioré la visualistion de cette date
					text +=	"            <td>"+str(player.friend)+"</td>\n" #amélioré la visualistion de cette date
					text +=	"            <td>"+str(player.ech)+"</td>\n" #amélioré la visualistion de cette date
					text +=	"            <td>"+str(player.ok)+"</td>\n" #amélioré la visualistion de cette date
					text +=	"            <td>"+str(player.ca)+"</td>\n" #amélioré la visualistion de cette date
					text +=	"            <td>"+str(player.syn)+"</td>\n" #amélioré la visualistion de cette date
			text +=	"          </tr>\n"
		text +=	"        </table>\n"
		text +=	"      </center>\n"
		text +=	"    </body>\n"
		text +=	"  </html>\n"
		return text
		
		self.last_seen = time.time()
		self.pkm = ""
		self.friend = ""
		self.ech = 0
		self.ok  = 0
		self.ca  = 0
		self.syn = 0

	def render_POST(self, request):
		'''
			Génére une réponse aux requettes POST
			
			Toutes les requette sont vérifiées et en cas de requette mal formée log de niveau Warning
			La proction contre l'auto échange est plus strict mais désactivable.
		'''
		
		self.logger.debug("Requette POST recue : %s", request.args)
		
		# Mise à jour des joueurs présent à chaque requettes reçus
		self.update()
		
		# on fait une fonction pour avoir un return,
		# donc un code plus propreet plus simple
		ret = self.process(request)
		
		self.logger.debug("Retour -> %s",ret)
		return ret
		
	def process(self, request):
		'''
			Traite les requetes POST
			
			Le traitement aurai pu se faire dans la fonction render_POST mais pour la
			lisibilité et la simplicité du code on fait une fonction à part (complexité
			au niveau des "if" ibriqués et des "return")
		'''
		session = {}
		session['cles'] = request.args.keys()
		
		# On vérifie que le mode est spécifié
		if "mode" in session['cles']:
			if len(request.args["mode"])!=1:
				session['mode_error'] = "Requette invalide : plusieurs modes specifies" + str(request.args["mode"])
			session['mode'] = request.args["mode"][0]
			self.logger.debug("Requette POST de type : %s",session['mode'])
		else:
			session['mode_error'] = "Requette invalide : aucun mode specifie"

		if 'mode_error' in session:
			self.logger.warning(session['mode_error'])
			return session['mode_error']

		# On gére les modes suivant ce qui est spécifié dans la requette POST
		if session['mode'] == "connect":
			# requette de "connexion" au serveur (envoyer par le client tant que 
			# ce denier n'as pas selectioner de joueurs pour faire l'échange)
			
			#on vérifie le code perso
			if not self.check_list(['monCode'],session,request):
				return session['check_error']
					
			# Ajout du joueur à la liste si pas déja présent
			# Mise à jour des infos dans le cas contraire
			if session['monCode'] not in self.player_list:
				self.player_list[session['monCode']]=Player(session['monCode'])
				self.logger.info("Connexion de : %s", self.player_list[session['monCode']])
			else:
				self.player_list[session['monCode']].seen()
				self.logger.debug("Mise a jour de %s", self.player_list[session['monCode']])
				
			# On renvoie la liste des Codes de tous les joueurs présents
			return str(self.player_list.keys())
			
		elif session['mode'] == "select":
			# Requette de Demande d'échange
			
			# on vérifie le code perso et le code ami
			if not self.check_list(['monCode','sonCode'],session,request):
				self.logger.warning(session['check_error'])
				return session['check_error']
			
			player_1 = self.player_list[session['monCode']]
			player_2 = self.player_list[session['sonCode']]
			self.logger.info("%s demande echange a %s", player_1, player_2)
			player_1.seen()
			player_1.set_ech()
			player_1.friend = player_2
			
			if time.time() - player_2.ech < self.timeout and player_2.friend == player_1:
				self.logger.info("%s accepte %s", player_1, player_2)
				return "true"
			else:
				self.logger.info("%s attend %s", player_1, player_2)
				return ""
			
		elif session['mode'] == "sent":
			# on vérifie le code perso, le code ami et les data sur le pokemon
			if not self.check_list(['monCode','sonCode','pokemon'],session,request):
				self.logger.warning(session['check_error'])
				return session['check_error']
			
			player_1 = self.player_list[session['monCode']]
			player_2 = self.player_list[session['sonCode']]
			
			# Interdiction d'auto échange se basant sur l'id
			#if player_1.id == player_2.id:							# L'ancien système se base uniquement sur le code
			#	player_1.reset_all()								# ID_pseudo est peu être contourner par un changement
			#	logger.warning("Auto echange %s", player_1)			# de pseudo donc désactivation dans ce script
			#	return "Auto echange interdit"						# Décomenter pour réactiver

			player_1.set_ech()
			logger.info("%s envoie son pokemon", player_1)
			if player_1.pkm !="" and  time.time() - player_2.ech < self.timeout and player_2.friend == player_1.id:
				self.logger.debug("%s regarde le pokemon de %s", player_1, player_2)
				return player_2.pkm
			else:
				self.logger.debug("%s attend le pokemon de %s", player_1, player_2)
				return ""
				
		elif session['mode'] == "update":
			# on vérifie le code perso et le code ami
			if not self.check_list(['monCode','sonCode'],session,request):
				self.logger.warning(session['check_error'])
				return session['check_error']
			
			player_1 = self.player_list[session['monCode']]
			player_2 = self.player_list[session['sonCode']]
			
			# Interdiction d'auto échange se basant sur l'id
			#if player_1.id == player_2.id:							# L'ancien système se base uniquement sur le code
			#	player_1.reset_all()								# ID_pseudo est peu être contourner par un changement
			#	logger.warning("Auto echange %s", player_1)			# de pseudo donc désactivation dans ce script
			#	return "Auto echange interdit"						# Décomenter pour réactiver
			
			player_1.set_ech()
			self.logger.info("%s envoie son pokemon", player_1)
			if player_2.pkm !="" and player_2.ech !=0 and time.time() - player_2.ech < self.timeout and player_2.friend == player_1.id:
				self.logger.info("%s regarde le pokemon de %s", player_1, player_2)
				return player_1.pkm
			else:
				self.logger.info("%s attend le pokemon de %s", player_1, player_2)
				return ""
				
		elif session['mode'] == "valid":
			# on vérifie le code perso et le code ami
			if not self.check_list(['monCode','sonCode'],session,request):
				self.logger.warning(session['check_error'])
				return session['check_error']
			
			player_1 = self.player_list[session['monCode']]
			player_2 = self.player_list[session['sonCode']]
			
			# Interdiction d'auto échange se basant sur l'id
			#if player_1.id == player_2.id:							# L'ancien système se base uniquement sur le code
			#	player_1.reset_all()								# ID_pseudo est peu être contourner par un changement
			#	logger.warning("Auto echange %s", player_1)			# de pseudo donc désactivation dans ce script
			#	return "Auto echange interdit"						# Décomenter pour réactiver
			
			player_1.seen()
			player_1.set_ok()
			
			if player_2.ca !=0 and player_2.ca > player_2.ech and player_2.friend == player_1.id:
				return "false"
			elif player_2.ok !=0 and time.time() - player_2.ok < self.timeout and player_2.friend == player_1.id:
				return "true"
			else:
				return ""
				
		elif session['mode'] == "cancel":
			# on vérifie le code perso et le code ami
			if not self.check_list(['monCode','sonCode'],session,request):
				self.logger.warning(session['check_error'])
				return session['check_error']
			
			player_1 = self.player_list[session['monCode']]
			player_2 = self.player_list[session['sonCode']]
			
			# Interdiction d'auto échange se basant sur l'id
			# L'ancien système se base uniquement sur le code
			# ID_pseudo est peu être contourner par un changement
			# de pseudo donc ici on se base sur l'id uniquement
			if self.checkAuto and  player_1.id == player_2.id:							
				player_1.reset_all()								
				logger.warning("Auto echange %s", player_1)			
				return "Auto echange interdit"						
			
			player_1.seen()
			player_1.set_ca()
			
			return "true"
			
		elif session['mode'] == "synchro":
			if not self.check_list(['monCode','sonCode'],session):
				self.logger.warning(session['check_error'])
				return session['check_error']
				
			player_1 = self.player_list[session['monCode']]
			player_2 = self.player_list[session['sonCode']]
			
			# Interdiction d'auto échange se basant sur l'id
			# L'ancien système se base uniquement sur le code
			# ID_pseudo est peu être contourner par un changement
			# de pseudo donc ici on se base sur l'id uniquement
			if self.checkAuto and  player_1.id == player_2.id:							
				player_1.reset_all()								
				logger.warning("Auto echange %s", player_1)			
				return "Auto echange interdit"						
				
			player_1.set_syn()
			if time.time() - player_2.syn < self.timeout :
				return "true"
			else:
				return ""
				
		elif session['mode'] == "delete":
			# Mode 
			if not self.check_list(['monCode'],session,request):
				self.logger.warning(session['check_error'])
				return session['check_error']
			player_1 = self.player_list[session['monCode']]
			
			if self.check_list(['sonCode'],session,request):
				player_2 = self.player_list[session['sonCode']]
				if player_2.friend == player_1.id:
					player_2.reset_all()
			
			if session['monCode'] in self.player_list:
				self.logger.info("Deconexion de %s", player_1)
				del player_1, self.player_list[session['monCode']]
			return ""
		
		else:
			# Mode non autorisé
			session['mode_error'] = "Requette invalide : mode '%s' non autorise " % request.args["mode"][0]
			self.logger.warning(session['mode_error'])
			return session['mode_error']
		
	def check_list(self,arg_list,session,request):
		'''
			Vérifie que les argumets de la list arg_list sont bien présent en 1 seul exemplaire dans la requette 
			Si l'argument et de type Code on vérifie aussi sa validité
		'''
		for arg in arg_list:
			if arg in session['cles']:
				if len(request.args[arg])!=1:
					session['check_error'] = "Requette '%s' invalide : l'argument '%s' est present %s fois (%s)" %(session['mode'], arg, len(request.args["monCode"]), str(request.args["monCode"]))
					return False
				else:
					if arg == 'monCode' or arg == 'sonCode':
						if not self.check_code(arg,session,request):
							return False
					session[arg]=request.args[arg][0]
			else:
				session['check_error'] = "Requette '%s' invalide : l'argument '%s' est manquant" % (session['mode'], arg)
				return False
		return True
		
	def check_code(self,arg,session,request):
		'''Vérifie que le code est Valide'''
		code = request.args[arg][0]
		#check format id_Pseudo
		if '_' not in code:
			session['check_error'] = "Requette '%s' invalide : '%s' n'est pas un code valide pour '%s'" % (session['mode'], code, arg)
			return False
		
		id, name = code.split("_",1)
		
		#check que id est bien un nombre
		if not id.isdigit():
			session['check_error'] = "Requette '%s' invalide : '%s' n'est pas un code valide pour '%s' (l'id n'est pas un nombre !)" % (session['mode'], code, arg)
			return False
		
		#check char spec
		if not name.isalnum():
			for char in name:
				if char not in ['_','$','-'] :
					session['check_error'] = "Requette '%s' invalide : '%s' n'est pas un code valide pour '%s' (le nom contient des char speciaux !)" % (session['mode'], code, arg)
					return False
			
		#Check de connection du joueur (bug en select)
		if (session['mode'] not in ['connect','delete']) and (code not in self.player_list) :
			session['check_error'] = "Requette '%s' invalide : {%s : %s} ne correspond pas a un joueur conecte" % (session['mode'], arg, code)
			return False
		
		return True


def main():
	#config par défaut puis parsing des args
	TIMEOUT 	= 3600 										# timeout des joueurs (60s en temps normal suffisent,3600 pourle debug)
	LOG_CONF 	= 'log.cfg'									# Fichier de configuration du log	
	CHECK_AUTO 	= False										# Interdire les auto-échanges
	MASTER_CODE = '{0:x}'.format(random.getrandbits(64))	# Master code aléatoire
	for arg in sys.argv[1:]:
		var = arg.split('=')
		if len(var) == 2:
			if var[0]=='timeout' and var[1].isdigit:
				TIMEOUT = int(var[1])
			elif var[0]=='log_conf':
				LOG_CONF=var[1]
			elif var[0]=='check_auto' and var[1] in ['true','false']:
				CHECK_AUTO = ('true'==var[1])
			elif var[0]=='master_code':
				MASTER_CODE = var[1]
			else:
				print "Argument Invalide !", arg
		else:
			print "Argument Invalide !", arg
	
	# Lancement du serveur à la page index.php et sur le port 80 (fixé par le jeu)
	root = Resource()
	root.putChild("index.php", Serveur(TIMEOUT,LOG_CONF,CHECK_AUTO,MASTER_CODE))
	factory = Site(root)
	reactor.listenTCP(80, factory)
	reactor.run()


if __name__ == '__main__':
    main()