# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint


#################
# Team creation#
#################

def createTeam(firstIndex, secondIndex, isRed,
               first='OffensiveReflexAgent', second='DefensiveReflexAgent'):
    """
    This function should return a list of two agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.  isRed is True if the red team is being created, and
    will be False if the blue team is being created.
    As a potentially helpful development aid, this function can take
    additional string-valued keyword arguments ("first" and "second" are
    such arguments in the case of this function), which will come from
    the --redOpts and --blueOpts command-line arguments to capture.py.
    For the nightly contest, however, your team will be created without
    any extra arguments, so you should make sure that the default
    behavior is what you want for the nightly contest.
    """
    return [eval(first)(firstIndex), eval(second)(secondIndex)]


##########
# Agents #
##########


class DummyAgent(CaptureAgent):
    '''
    Methods inherited from the baselineTeam.py
    '''

    def getSuccessor(self, gameState, action):
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):

            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):
        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        features['successorScore'] = self.getScore(successor)
        return features

    def getWeights(self, gameState, action):
        return {'successorScore': 1.0}


class OffensiveReflexAgent(DummyAgent):

    def __init__(self, index):
        CaptureAgent.__init__(self, index)

        self.counter = 0
        self.eatenFood = 0
        self.hasStopped = 0
        self.attack = 0
        self.goHome = 0
        self.targetMode = None
        self.lastFood = []
        self.presentFoodList = []
        self.initialTarget = []

    def registerInitialState(self, gameState):
        self.currentFoodSize = 9999
        self.initialFoodNum = len(self.getFood(gameState).asList())
        CaptureAgent.registerInitialState(self, gameState)
        self.initPosition = gameState.getAgentState(self.index).getPosition()

        layoutInfo = []
        x = (gameState.data.layout.width - 2) // 2
        if not self.red:
            x += 1
        y = (gameState.data.layout.height - 2) // 2
        layoutInfo.extend((gameState.data.layout.width, gameState.data.layout.height, x, y))

        self.initialTarget = []

        for i in range(1, layoutInfo[1] - 1):
            if not gameState.hasWall(layoutInfo[2], i):
                self.initialTarget.append((layoutInfo[2], i))    

    def chooseAction(self, gameState):
        self.presentCoordinates = gameState.getAgentState(self.index).getPosition()

        if self.presentCoordinates == self.initPosition:
            self.hasStopped = 1
        if self.presentCoordinates == self.initialTarget[0]:
            self.hasStopped = 0

        if self.hasStopped == 1:
            legalActions = gameState.getLegalActions(self.index)
            legalActions.remove(Directions.STOP)

            distanceToTarget = []
            shortestDistance = 9999
            for i in range(0, len(legalActions)):
                action = legalActions[i]
                nextState = gameState.generateSuccessor(self.index, action)
                nextPosition = nextState.getAgentPosition(self.index)
                distance = self.getMazeDistance(nextPosition, self.initialTarget[0])
                distanceToTarget.append(distance)
                if (distance < shortestDistance):
                    shortestDistance = distance

            bestActionsList = [a for a, distance in zip(legalActions, distanceToTarget) if distance == shortestDistance]
            bestAction = random.choice(bestActionsList)

            return bestAction

        if self.hasStopped == 0:
            self.presentFoodList = self.getFood(gameState).asList()
           
            if len(self.presentFoodList) < len(self.lastFood):
                self.goHome = 1
            self.lastFood = self.presentFoodList
            

            if not gameState.getAgentState(self.index).isPacman:
                self.goHome = 0

            remainingFoodSize = len(self.getFood(gameState).asList())

            if remainingFoodSize == self.currentFoodSize:
                self.counter += 1
            else:
                self.currentFoodSize = remainingFoodSize
                self.counter = 0
            if gameState.getInitialAgentPosition(self.index) == gameState.getAgentState(self.index).getPosition():
                self.counter = 0
            if self.counter > 20:
                self.attack = 1
            else:
                self.attack = 0

            actions = gameState.getLegalActions(self.index)
            actions.remove(Directions.STOP)

            
            distanceToEnemy = 9999
            enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
            invaders = [a for a in enemies if not a.isPacman and a.getPosition() != None and a.scaredTimer == 0]
            if len(invaders) > 0:
                distanceToEnemy = min([self.getMazeDistance(self.presentCoordinates, a.getPosition()) for a in invaders])
   
            values = [self.evaluate(gameState, a) for a in actions]
            maxValue = max(values)
            bestActions = [a for a, v in zip(actions, values) if v == maxValue]
            foodLeft = len(self.getFood(gameState).asList())
            myTeam = [gameState.getAgentState(i) for i in self.getTeam(gameState)]
            
            if not myTeam[0].isPacman and not myTeam[1].isPacman and self.index == 0:
                self.numFood = foodLeft
            elif myTeam[0].isPacman and not myTeam[1].isPacman and self.index == 0:
                self.foodEaten = self.numFood - foodLeft
                if (self.foodEaten == round(self.initialFoodNum / 10)):
                    bestDist = 9999
                    for action in actions:
                        successor = self.getSuccessor(gameState, action)
                        pos2 = successor.getAgentPosition(self.index)
                        dist = self.getMazeDistance(self.initPosition, pos2)
                        if dist < bestDist:
                            bestAction = action
                            bestDist = dist
                    return bestAction

            return random.choice(bestActions)

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        position = successor.getAgentState(self.index).getPosition()
        foodList = self.getFood(successor).asList()
        features['successorScore'] = -len(foodList)

        if successor.getAgentState(self.index).isPacman:
            features['offence'] = 1
        else:
            features['offence'] = 0

        if foodList:
            features['foodDistance'] = min([self.getMazeDistance(position, food) for food in foodList])

        opponentsList = []
        disToGhost = []
        opponentsList = self.getOpponents(successor)

        for i in range(len(opponentsList)):
            enemy = successor.getAgentState(opponentsList[i])
            if not enemy.isPacman and enemy.getPosition() != None:
                ghostPos = enemy.getPosition()
                disToGhost.append(self.getMazeDistance(position, ghostPos))

        if len(disToGhost) > 0:

            if min(disToGhost) < 5:
                features['distanceToGhost'] = min(disToGhost)
            else:
                features['distanceToGhost'] = 0

        return features

    def getWeights(self, gameState, action):

        if self.attack:
            if self.goHome:
                return {'offence': 0, 'successorScore': 100, 'foodDistance': -1, 'distancesToGhost': 100}
            else:
                return {'offence': 300, 'successorScore': 100, 'foodDistance': -1, 'distancesToGhost': 100}
        else:
            successor = self.getSuccessor(gameState, action)
            enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
            invaders = [a for a in enemies if not a.isPacman and a.getPosition() != None]
            if len(invaders) > 0:
                if invaders[-1].scaredTimer > 0:
                    return {'offence': 0, 'successorScore': 100, 'foodDistance': -1, 'distancesToGhost': 0}
                return {'offence': 0, 'successorScore': 100, 'foodDistance': -1, 'distancesToGhost': 100}


class DefensiveReflexAgent(DummyAgent):

    def __init__(self, index):
        CaptureAgent.__init__(self, index)
        self.target = None
        self.previousFood = []
        self.counter = 0

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.setPatrolPoint(gameState)

    def setPatrolPoint(self, gameState):
        '''
        Look for center of the maze for patrolling
        '''
        x = (gameState.data.layout.width - 2) // 2
        if not self.red:
            x += 1
        self.patrolPoints = []
        for i in range(1, gameState.data.layout.height - 1):
            if not gameState.hasWall(x, i):
                self.patrolPoints.append((x, i))

        for i in range(len(self.patrolPoints)):
            if len(self.patrolPoints) > 2:
                self.patrolPoints.remove(self.patrolPoints[0])
                self.patrolPoints.remove(self.patrolPoints[-1])
            else:
                break

    def chooseAction(self, gameState):

        position = gameState.getAgentPosition(self.index)
        if position == self.target:
            self.target = None
        invaders = []
        nearestInvader = []
        minDistance = float("inf")        
        opponentsPositions = self.getOpponents(gameState)
        i = 0
        while i != len(opponentsPositions):
            opponentPos = opponentsPositions[i]
            opponent = gameState.getAgentState(opponentPos)
            if opponent.isPacman and opponent.getPosition() != None:
                opponentPos = opponent.getPosition()
                invaders.append(opponentPos)
            i += 1

       
        if len(invaders) > 0:
            for oppPosition in invaders:
                dist = self.getMazeDistance(oppPosition, position)
                if dist < minDistance:
                    minDistance = dist
                    nearestInvader.append(oppPosition)
            self.target = nearestInvader[-1]

        self.previousFood = self.getFoodYouAreDefending(gameState).asList()
        self.target = random.choice(self.patrolPoints)
        agentActions = []
        actions = gameState.getLegalActions(self.index)
        
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        actions.remove(Directions.STOP)

        for i in range(0, len(actions) - 1):
            if rev == actions[i]:
                actions.remove(rev)

        for i in range(len(actions)):
            a = actions[i]
            newState = gameState.generateSuccessor(self.index, a)
            if not newState.getAgentState(self.index).isPacman:
                agentActions.append(a)

        if len(agentActions) == 0:
            self.counter = 0
        else:
            self.counter = self.counter + 1
        if self.counter > 4 or self.counter == 0:
            agentActions.append(rev)

        defActions = []
        values = []

        i = 0        
        while i < len(agentActions):
            a = agentActions[i]
            nextState = gameState.generateSuccessor(self.index, a)
            newpos = nextState.getAgentPosition(self.index)
            defActions.append(a)
            values.append(self.getMazeDistance(newpos, self.target))
            i += 1

        best = min(values)
        bestActions = [a for a, v in zip(defActions, values) if v == best]
        bestAction = random.choice(bestActions)
        return bestAction
