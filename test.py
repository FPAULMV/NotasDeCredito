from fns import SqlResources
if __name__ == '__main__':

    creditnotes = SqlResources()
    print(f"Las notas de credito registradas son:\n{creditnotes.registred_nc}")